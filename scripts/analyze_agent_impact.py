#!/usr/bin/env python3
"""
Agent Ecosystem Impact Analyzer

Analyzes code changes and determines which agents in the ecosystem
need to be reviewed or updated.

Usage:
    python scripts/analyze_agent_impact.py --diff <git_diff_file>
    python scripts/analyze_agent_impact.py --commit <commit_sha>
    python scripts/analyze_agent_impact.py --pr <pr_number>

Example:
    git diff HEAD~1 > changes.diff
    python scripts/analyze_agent_impact.py --diff changes.diff
"""
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    file_patterns: List[str]
    keyword_patterns: List[str]
    description: str
    priority: str = "medium"


@dataclass
class ImpactResult:
    """Result of impact analysis for an agent."""
    agent_name: str
    status: str  # "REVIEW_NEEDED", "UPDATE_REQUIRED", "OK"
    matched_files: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0


# Agent configuration - maps agents to file patterns and keywords
AGENT_CONFIGS = [
    AgentConfig(
        name="contract-validator",
        file_patterns=[
            "backend/app/services/contract_validator_service.py",
            "backend/app/services/kobetsu_service.py",
            "backend/app/schemas/kobetsu*.py",
            "backend/app/models/kobetsu_keiyakusho.py",
        ],
        keyword_patterns=[
            r"16.*fields?",
            r"労働者派遣法",
            r"validation",
            r"required.*fields?",
            r"compliance.*score",
        ],
        description="Validates contracts against 16 legal fields",
        priority="high",
    ),
    AgentConfig(
        name="compliance-checker",
        file_patterns=[
            "backend/app/services/compliance_checker_service.py",
            "backend/app/api/v1/compliance.py",
        ],
        keyword_patterns=[
            r"compliance",
            r"audit",
            r"violation",
            r"法26条",
        ],
        description="Audits system for legal compliance",
        priority="high",
    ),
    AgentConfig(
        name="alert-manager",
        file_patterns=[
            "backend/app/services/alert_manager_service.py",
            "backend/scripts/run_scheduled_tasks.py",
        ],
        keyword_patterns=[
            r"alert",
            r"notification",
            r"expir",
            r"critical.*priority",
        ],
        description="Manages proactive alerts",
        priority="high",
    ),
    AgentConfig(
        name="document-generator",
        file_patterns=[
            "backend/app/services/kobetsu_pdf_service.py",
            "backend/app/services/kobetsu_excel_generator.py",
            "backend/app/services/dispatch_documents_service.py",
            "backend/app/services/treatment_document_service.py",
            "backend/app/api/v1/documents.py",
        ],
        keyword_patterns=[
            r"document",
            r"pdf",
            r"excel",
            r"template",
            r"generate.*docx?",
        ],
        description="Generates legal documents",
        priority="medium",
    ),
    AgentConfig(
        name="sync-resolver",
        file_patterns=[
            "backend/app/services/sync_resolver_service.py",
            "backend/app/services/import_service.py",
            "backend/app/api/v1/imports.py",
        ],
        keyword_patterns=[
            r"sync",
            r"conflict",
            r"import.*excel",
            r"resolution",
        ],
        description="Resolves data sync conflicts",
        priority="medium",
    ),
    AgentConfig(
        name="analytics-reporter",
        file_patterns=[
            "backend/app/api/v1/stats.py",
        ],
        keyword_patterns=[
            r"analytics",
            r"report",
            r"dashboard",
            r"metrics",
        ],
        description="Generates analytics reports",
        priority="low",
    ),
    AgentConfig(
        name="frontend",
        file_patterns=[
            "frontend/app/",
            "frontend/components/",
            "frontend/lib/",
        ],
        keyword_patterns=[
            r"component",
            r"page",
            r"useState",
            r"useQuery",
        ],
        description="Frontend development specialist",
        priority="medium",
    ),
    AgentConfig(
        name="backend",
        file_patterns=[
            "backend/app/api/",
            "backend/app/services/",
            "backend/app/core/",
        ],
        keyword_patterns=[
            r"@router",
            r"FastAPI",
            r"endpoint",
            r"service",
        ],
        description="Backend development specialist",
        priority="medium",
    ),
    AgentConfig(
        name="database",
        file_patterns=[
            "backend/app/models/",
            "backend/alembic/",
        ],
        keyword_patterns=[
            r"class.*Model",
            r"Column\(",
            r"relationship\(",
            r"migration",
        ],
        description="Database specialist",
        priority="high",
    ),
    AgentConfig(
        name="security",
        file_patterns=[
            "backend/app/core/security.py",
            "backend/app/api/v1/auth.py",
        ],
        keyword_patterns=[
            r"jwt",
            r"password",
            r"auth",
            r"token",
            r"security",
        ],
        description="Security specialist",
        priority="high",
    ),
]


class AgentImpactAnalyzer:
    """Analyzes code changes for agent ecosystem impact."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.agents_dir = self.project_root / ".claude" / "agents"

    def get_changed_files_from_diff(self, diff_content: str) -> List[str]:
        """Extract changed files from git diff output."""
        files = set()
        for line in diff_content.split("\n"):
            if line.startswith("diff --git"):
                # Extract file path from "diff --git a/path b/path"
                match = re.search(r"diff --git a/(.+) b/(.+)", line)
                if match:
                    files.add(match.group(2))
            elif line.startswith("+++"):
                # Extract from "+++ b/path"
                match = re.search(r"\+\+\+ b/(.+)", line)
                if match:
                    files.add(match.group(1))
        return list(files)

    def get_changed_files_from_commit(self, commit_sha: str) -> List[str]:
        """Get changed files from a specific commit."""
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            return [f for f in result.stdout.strip().split("\n") if f]
        except Exception as e:
            print(f"Error getting changed files: {e}", file=sys.stderr)
            return []

    def analyze_file_content(self, file_path: str) -> str:
        """Read file content if it exists."""
        full_path = self.project_root / file_path
        if full_path.exists():
            try:
                return full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return ""
        return ""

    def match_patterns(self, content: str, patterns: List[str]) -> List[str]:
        """Find matching patterns in content."""
        matches = []
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                matches.append(pattern)
        return matches

    def analyze_impact(self, changed_files: List[str]) -> Dict[str, ImpactResult]:
        """Analyze impact on agents based on changed files."""
        results = {}

        for agent_config in AGENT_CONFIGS:
            matched_files = []
            matched_keywords = []

            # Check file patterns
            for changed_file in changed_files:
                for pattern in agent_config.file_patterns:
                    if pattern.endswith("/"):
                        # Directory pattern
                        if changed_file.startswith(pattern):
                            matched_files.append(changed_file)
                            break
                    else:
                        # File pattern (support wildcards)
                        import fnmatch
                        if fnmatch.fnmatch(changed_file, pattern):
                            matched_files.append(changed_file)
                            break

            # Check keyword patterns in changed files
            for changed_file in matched_files:
                content = self.analyze_file_content(changed_file)
                matches = self.match_patterns(content, agent_config.keyword_patterns)
                matched_keywords.extend(matches)

            # Determine status
            if matched_files:
                if len(matched_files) >= 3 or len(set(matched_keywords)) >= 2:
                    status = "UPDATE_REQUIRED"
                    confidence = 0.9
                else:
                    status = "REVIEW_NEEDED"
                    confidence = 0.7

                results[agent_config.name] = ImpactResult(
                    agent_name=agent_config.name,
                    status=status,
                    matched_files=list(set(matched_files)),
                    matched_keywords=list(set(matched_keywords)),
                    recommendation=self._generate_recommendation(agent_config, status),
                    confidence=confidence,
                )

        return results

    def _generate_recommendation(self, config: AgentConfig, status: str) -> str:
        """Generate recommendation for an agent."""
        if status == "UPDATE_REQUIRED":
            return f"Update {config.name}.md to reflect significant changes in {config.description.lower()}"
        else:
            return f"Review {config.name}.md - minor changes detected in related files"

    def generate_report(self, results: Dict[str, ImpactResult], format: str = "text") -> str:
        """Generate impact report."""
        if format == "json":
            return json.dumps(
                {
                    name: {
                        "status": r.status,
                        "matched_files": r.matched_files,
                        "matched_keywords": r.matched_keywords,
                        "recommendation": r.recommendation,
                        "confidence": r.confidence,
                    }
                    for name, r in results.items()
                },
                indent=2,
            )

        # Text format
        lines = []
        lines.append("=" * 60)
        lines.append("AGENT ECOSYSTEM IMPACT ANALYSIS")
        lines.append("=" * 60)
        lines.append("")

        if not results:
            lines.append("No agents directly affected by these changes.")
        else:
            # Group by status
            update_required = [r for r in results.values() if r.status == "UPDATE_REQUIRED"]
            review_needed = [r for r in results.values() if r.status == "REVIEW_NEEDED"]

            if update_required:
                lines.append("REQUIRES UPDATE:")
                for r in update_required:
                    lines.append(f"  - {r.agent_name}")
                    lines.append(f"      Files: {', '.join(r.matched_files[:3])}")
                    if r.matched_keywords:
                        lines.append(f"      Keywords: {', '.join(r.matched_keywords[:3])}")
                    lines.append(f"      Recommendation: {r.recommendation}")
                lines.append("")

            if review_needed:
                lines.append("NEEDS REVIEW:")
                for r in review_needed:
                    lines.append(f"  - {r.agent_name}")
                    lines.append(f"      Files: {', '.join(r.matched_files[:3])}")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze agent ecosystem impact")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--diff", help="Path to git diff file")
    group.add_argument("--commit", help="Commit SHA to analyze")
    group.add_argument("--files", nargs="+", help="List of changed files")

    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    analyzer = AgentImpactAnalyzer(args.project_root)

    # Get changed files
    if args.diff:
        with open(args.diff, "r") as f:
            diff_content = f.read()
        changed_files = analyzer.get_changed_files_from_diff(diff_content)
    elif args.commit:
        changed_files = analyzer.get_changed_files_from_commit(args.commit)
    else:
        changed_files = args.files

    print(f"Analyzing {len(changed_files)} changed files...", file=sys.stderr)

    # Analyze impact
    results = analyzer.analyze_impact(changed_files)

    # Generate report
    report = analyzer.generate_report(results, args.format)
    print(report)

    # Exit with code based on impact
    if any(r.status == "UPDATE_REQUIRED" for r in results.values()):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
