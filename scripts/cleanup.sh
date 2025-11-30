#!/bin/bash

#############################################################################
# System Cleanup Script for UNS-Kobetsu System
#
# Usage:
#   ./scripts/cleanup.sh              # Run all cleanup tasks
#   ./scripts/cleanup.sh --logs       # Clean only logs
#   ./scripts/cleanup.sh --docker     # Clean only Docker resources
#   ./scripts/cleanup.sh --temp       # Clean only temporary files
#   ./scripts/cleanup.sh --dry-run    # Show what would be cleaned
#
# Features:
#   - Cleans old log files
#   - Removes Docker unused images, containers, volumes
#   - Cleans temporary files and caches
#   - Shows disk usage before and after
#############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_RETENTION_DAYS=7
DRY_RUN=false
CLEAN_LOGS=false
CLEAN_DOCKER=false
CLEAN_TEMP=false
CLEAN_ALL=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --logs)
            CLEAN_LOGS=true
            CLEAN_ALL=false
            shift
            ;;
        --docker)
            CLEAN_DOCKER=true
            CLEAN_ALL=false
            shift
            ;;
        --temp)
            CLEAN_TEMP=true
            CLEAN_ALL=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --days)
            LOG_RETENTION_DAYS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --logs       Clean only log files"
            echo "  --docker     Clean only Docker resources"
            echo "  --temp       Clean only temporary files"
            echo "  --dry-run    Show what would be cleaned without doing it"
            echo "  --days N     Keep N days of logs (default: 7)"
            echo "  --help       Show this help message"
            echo ""
            echo "If no options specified, all cleanup tasks are performed."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Enable all if --all or no specific options
if [ "$CLEAN_ALL" = true ]; then
    CLEAN_LOGS=true
    CLEAN_DOCKER=true
    CLEAN_TEMP=true
fi

# Function to get directory size
get_size() {
    if [ -d "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

# Function to execute or show command (for dry-run)
execute_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] $*"
    else
        eval "$@"
    fi
}

echo -e "${BLUE}=== UNS-Kobetsu System Cleanup ===${NC}"
echo "Timestamp: $(date)"
[ "$DRY_RUN" = true ] && echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
echo ""

# Show initial disk usage
echo "Current disk usage:"
df -h / | grep -E '^/|Filesystem'
echo ""

# Store initial sizes
INITIAL_DOCKER_SIZE=$(docker system df 2>/dev/null | grep "RECLAIMABLE" | tail -1 | awk '{print $4}' || echo "0")

#############################################################################
# Clean Log Files
#############################################################################
if [ "$CLEAN_LOGS" = true ]; then
    echo -e "${GREEN}Cleaning log files...${NC}"

    # Backend logs
    BACKEND_LOGS="./backend/logs"
    if [ -d "$BACKEND_LOGS" ]; then
        echo "  Backend logs (keeping last $LOG_RETENTION_DAYS days):"
        OLD_LOGS=$(find "$BACKEND_LOGS" -name "*.log*" -type f -mtime +$LOG_RETENTION_DAYS 2>/dev/null || true)
        if [ -n "$OLD_LOGS" ]; then
            echo "$OLD_LOGS" | while read -r file; do
                echo "    Removing: $(basename "$file")"
                execute_cmd "rm -f '$file'"
            done
        else
            echo "    No old logs to remove"
        fi
    fi

    # Frontend logs
    FRONTEND_LOGS="./frontend/.next"
    if [ -d "$FRONTEND_LOGS" ]; then
        echo "  Frontend build cache:"
        SIZE=$(get_size "$FRONTEND_LOGS/cache")
        if [ "$SIZE" != "0" ]; then
            echo "    Cleaning .next/cache ($SIZE)"
            execute_cmd "rm -rf '$FRONTEND_LOGS/cache'"
        else
            echo "    No cache to clean"
        fi
    fi

    # Docker container logs
    echo "  Docker container logs:"
    if [ "$DRY_RUN" = false ]; then
        docker compose logs --tail=0 2>/dev/null || echo "    No running containers"
    else
        echo "    [DRY-RUN] Would truncate Docker container logs"
    fi

    # Python cache
    echo "  Python cache:"
    PYCACHE_COUNT=$(find ./backend -type d -name "__pycache__" 2>/dev/null | wc -l || echo "0")
    if [ "$PYCACHE_COUNT" -gt 0 ]; then
        echo "    Removing $PYCACHE_COUNT __pycache__ directories"
        execute_cmd "find ./backend -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"
    else
        echo "    No Python cache to clean"
    fi

    echo ""
fi

#############################################################################
# Clean Docker Resources
#############################################################################
if [ "$CLEAN_DOCKER" = true ]; then
    echo -e "${GREEN}Cleaning Docker resources...${NC}"

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${YELLOW}  Docker is not running. Skipping Docker cleanup.${NC}"
    else
        # Stop containers first
        echo "  Checking for stopped containers..."
        STOPPED_CONTAINERS=$(docker ps -aq --filter "status=exited" | wc -l)
        if [ "$STOPPED_CONTAINERS" -gt 0 ]; then
            echo "    Found $STOPPED_CONTAINERS stopped containers"
            execute_cmd "docker container prune -f"
        else
            echo "    No stopped containers"
        fi

        # Clean unused images
        echo "  Checking for unused images..."
        UNUSED_IMAGES=$(docker images -q --filter "dangling=true" | wc -l)
        if [ "$UNUSED_IMAGES" -gt 0 ]; then
            echo "    Found $UNUSED_IMAGES dangling images"
            execute_cmd "docker image prune -f"
        else
            echo "    No dangling images"
        fi

        # Clean unused volumes (be careful!)
        echo "  Checking for unused volumes..."
        UNUSED_VOLUMES=$(docker volume ls -q --filter "dangling=true" | wc -l)
        if [ "$UNUSED_VOLUMES" -gt 0 ]; then
            echo -e "${YELLOW}    Found $UNUSED_VOLUMES unused volumes${NC}"
            echo "    NOTE: Skipping volume cleanup to prevent data loss"
            echo "    To clean volumes manually, run: docker volume prune"
        else
            echo "    No unused volumes"
        fi

        # Clean build cache
        echo "  Checking Docker build cache..."
        if [ "$DRY_RUN" = false ]; then
            docker builder prune -f --filter "until=24h" 2>/dev/null || echo "    No build cache to clean"
        else
            echo "    [DRY-RUN] Would clean Docker build cache older than 24h"
        fi

        # Show Docker disk usage
        if [ "$DRY_RUN" = false ]; then
            echo ""
            echo "  Docker disk usage after cleanup:"
            docker system df
        fi
    fi

    echo ""
fi

#############################################################################
# Clean Temporary Files
#############################################################################
if [ "$CLEAN_TEMP" = true ]; then
    echo -e "${GREEN}Cleaning temporary files...${NC}"

    # Upload directory
    UPLOAD_DIR="./backend/uploads"
    if [ -d "$UPLOAD_DIR" ]; then
        echo "  Upload directory:"
        OLD_UPLOADS=$(find "$UPLOAD_DIR" -type f -mtime +30 2>/dev/null | wc -l || echo "0")
        if [ "$OLD_UPLOADS" -gt 0 ]; then
            echo "    Removing $OLD_UPLOADS files older than 30 days"
            execute_cmd "find '$UPLOAD_DIR' -type f -mtime +30 -delete 2>/dev/null || true"
        else
            echo "    No old uploads to remove"
        fi
    fi

    # Output directory
    OUTPUT_DIR="./backend/output"
    if [ -d "$OUTPUT_DIR" ]; then
        echo "  Output directory:"
        OLD_OUTPUT=$(find "$OUTPUT_DIR" -type f -mtime +7 2>/dev/null | wc -l || echo "0")
        if [ "$OLD_OUTPUT" -gt 0 ]; then
            echo "    Removing $OLD_OUTPUT files older than 7 days"
            execute_cmd "find '$OUTPUT_DIR' -type f -mtime +7 -delete 2>/dev/null || true"
        else
            echo "    No old output files to remove"
        fi
    fi

    # NPM cache
    NPM_CACHE="./frontend/node_modules/.cache"
    if [ -d "$NPM_CACHE" ]; then
        SIZE=$(get_size "$NPM_CACHE")
        echo "  NPM cache:"
        if [ "$SIZE" != "0" ]; then
            echo "    Cleaning node_modules/.cache ($SIZE)"
            execute_cmd "rm -rf '$NPM_CACHE'"
        else
            echo "    No NPM cache to clean"
        fi
    fi

    # Pytest cache
    PYTEST_CACHE="./backend/.pytest_cache"
    if [ -d "$PYTEST_CACHE" ]; then
        SIZE=$(get_size "$PYTEST_CACHE")
        echo "  Pytest cache:"
        if [ "$SIZE" != "0" ]; then
            echo "    Cleaning .pytest_cache ($SIZE)"
            execute_cmd "rm -rf '$PYTEST_CACHE'"
        else
            echo "    No pytest cache to clean"
        fi
    fi

    # Coverage reports
    echo "  Coverage reports:"
    COV_FILES=$(find . -name ".coverage*" -o -name "htmlcov" -o -name "coverage.xml" 2>/dev/null | wc -l || echo "0")
    if [ "$COV_FILES" -gt 0 ]; then
        echo "    Removing $COV_FILES coverage files/directories"
        execute_cmd "find . -name '.coverage*' -o -name 'htmlcov' -o -name 'coverage.xml' | xargs rm -rf 2>/dev/null || true"
    else
        echo "    No coverage files to clean"
    fi

    echo ""
fi

#############################################################################
# Summary
#############################################################################
echo -e "${BLUE}=== Cleanup Summary ===${NC}"

# Show final disk usage
echo "Final disk usage:"
df -h / | grep -E '^/|Filesystem'

# Show Docker space reclaimed (if Docker cleanup was performed)
if [ "$CLEAN_DOCKER" = true ] && docker info >/dev/null 2>&1; then
    FINAL_DOCKER_SIZE=$(docker system df 2>/dev/null | grep "RECLAIMABLE" | tail -1 | awk '{print $4}' || echo "0")
    echo ""
    echo "Docker reclaimable space:"
    echo "  Before: $INITIAL_DOCKER_SIZE"
    echo "  After:  $FINAL_DOCKER_SIZE"
fi

echo ""
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN COMPLETE - No actual changes were made${NC}"
    echo "Run without --dry-run to perform the cleanup"
else
    echo -e "${GREEN}Cleanup completed successfully!${NC}"
fi

# Suggest additional manual cleanup
echo ""
echo "Additional manual cleanup options:"
echo "  • Remove old database backups: rm ./backups/kobetsu_backup_*.sql.gz"
echo "  • Clear Redis cache: docker exec uns-kobetsu-redis redis-cli FLUSHALL"
echo "  • Remove Docker volumes: docker volume prune (⚠️  CAUTION: Data loss!)"
echo "  • Full Docker cleanup: docker system prune -a (⚠️  CAUTION: Removes all!)"