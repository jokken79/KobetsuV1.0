'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { complianceApi, type ComplianceAuditReport, type ComplianceViolation, type AlertItem } from '@/lib/api'

// Icons
const Icons = {
  Shield: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  ),
  Warning: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  ),
  Play: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.986V5.653z" />
    </svg>
  ),
  Refresh: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
  ),
  Check: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  ExclamationCircle: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
    </svg>
  ),
  ChevronRight: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  ),
  Document: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  Building: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
    </svg>
  ),
  User: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
  ),
}

function ComplianceScore({ score }: { score: number }) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-600'
    if (score >= 70) return 'text-amber-600'
    return 'text-red-600'
  }

  const getScoreBg = (score: number) => {
    if (score >= 90) return 'bg-emerald-100 border-emerald-200'
    if (score >= 70) return 'bg-amber-100 border-amber-200'
    return 'bg-red-100 border-red-200'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 90) return '優良'
    if (score >= 70) return '要注意'
    return '要改善'
  }

  return (
    <div className="flex items-center gap-6">
      <div className={`relative w-32 h-32 rounded-full border-4 ${getScoreBg(score)} flex items-center justify-center`}>
        <div className="text-center">
          <span className={`text-4xl font-bold ${getScoreColor(score)}`}>{score}</span>
          <span className={`block text-sm ${getScoreColor(score)}`}>点</span>
        </div>
      </div>
      <div>
        <p className={`text-xl font-semibold ${getScoreColor(score)}`}>
          {getScoreLabel(score)}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          労働者派遣法第26条準拠
        </p>
      </div>
    </div>
  )
}

function SeverityBadge({ severity, count }: { severity: string; count: number }) {
  const styles: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-orange-100 text-orange-700 border-orange-200',
    medium: 'bg-amber-100 text-amber-700 border-amber-200',
    low: 'bg-blue-100 text-blue-700 border-blue-200',
  }

  const labels: Record<string, string> = {
    critical: '緊急',
    high: '高',
    medium: '中',
    low: '低',
  }

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border ${styles[severity] || styles.low}`}>
      <span className="text-2xl font-bold">{count}</span>
      <span className="text-sm font-medium">{labels[severity]}</span>
    </div>
  )
}

function ViolationCard({ violation }: { violation: ComplianceViolation }) {
  const priorityColors: Record<string, string> = {
    critical: 'border-l-red-500 bg-red-50',
    high: 'border-l-orange-500 bg-orange-50',
    medium: 'border-l-amber-500 bg-amber-50',
    low: 'border-l-blue-500 bg-blue-50',
  }

  const entityIcon = {
    contract: <Icons.Document />,
    factory: <Icons.Building />,
    employee: <Icons.User />,
  }[violation.entity_type] || <Icons.Document />

  const getEntityUrl = () => {
    switch (violation.entity_type) {
      case 'contract':
        return `/kobetsu/${violation.entity_id}`
      case 'factory':
        return `/factories/${violation.entity_id}`
      case 'employee':
        return `/employees/${violation.entity_id}`
      default:
        return '#'
    }
  }

  return (
    <div className={`p-4 border-l-4 ${priorityColors[violation.severity] || priorityColors.low} rounded-r-lg`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="text-gray-400 mt-0.5">
            {entityIcon}
          </div>
          <div>
            <p className="font-medium text-gray-900">
              {violation.message}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-gray-600">
                {violation.entity_name}
              </span>
              {violation.legal_reference && (
                <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                  {violation.legal_reference}
                </span>
              )}
            </div>
            {violation.remediation && (
              <p className="text-sm text-gray-500 mt-2">
                対応: {violation.remediation}
              </p>
            )}
          </div>
        </div>
        <Link
          href={getEntityUrl()}
          className="btn btn-sm btn-ghost flex-shrink-0"
        >
          詳細
          <Icons.ChevronRight />
        </Link>
      </div>
    </div>
  )
}

function AlertCard({ alert }: { alert: AlertItem }) {
  const priorityColors: Record<string, string> = {
    critical: 'border-l-red-500 bg-red-50',
    high: 'border-l-orange-500 bg-orange-50',
    medium: 'border-l-amber-500 bg-amber-50',
    low: 'border-l-blue-500 bg-blue-50',
    info: 'border-l-gray-500 bg-gray-50',
  }

  return (
    <Link
      href={alert.action_url}
      className={`block p-4 border-l-4 ${priorityColors[alert.priority] || priorityColors.info} rounded-r-lg hover:shadow-md transition-shadow`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-gray-900">{alert.title}</p>
          <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
        </div>
        {alert.expires_in_days !== undefined && (
          <span className={`text-sm font-medium flex-shrink-0 ${
            alert.expires_in_days <= 0 ? 'text-red-600' :
            alert.expires_in_days <= 7 ? 'text-orange-600' :
            'text-gray-500'
          }`}>
            {alert.expires_in_days > 0 ? `${alert.expires_in_days}日` : '期限切れ'}
          </span>
        )}
      </div>
    </Link>
  )
}

export default function CompliancePage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'overview' | 'violations' | 'alerts'>('overview')
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null)

  // Fetch compliance stats
  const { data: complianceData, isLoading: isLoadingCompliance } = useQuery({
    queryKey: ['compliance-stats'],
    queryFn: () => complianceApi.getCompliance(),
    refetchInterval: 60000,
  })

  // Fetch alerts
  const { data: alertsData, isLoading: isLoadingAlerts } = useQuery({
    queryKey: ['compliance-alerts'],
    queryFn: () => complianceApi.getAlerts(),
    refetchInterval: 60000,
  })

  // Run audit mutation
  const auditMutation = useMutation({
    mutationFn: () => complianceApi.runAudit(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-stats'] })
      queryClient.invalidateQueries({ queryKey: ['compliance-alerts'] })
      queryClient.invalidateQueries({ queryKey: ['audit-report'] })
    },
  })

  // Fetch audit report (when available)
  const { data: auditReport, isLoading: isLoadingReport } = useQuery({
    queryKey: ['audit-report'],
    queryFn: () => complianceApi.runAudit(),
    enabled: false, // Only run when explicitly triggered
  })

  const latestReport = auditMutation.data as ComplianceAuditReport | undefined

  // Filter violations by severity
  const filteredViolations = latestReport?.violations?.filter(
    v => !selectedSeverity || v.severity === selectedSeverity
  ) || []

  const filteredWarnings = latestReport?.warnings?.filter(
    v => !selectedSeverity || v.severity === selectedSeverity
  ) || []

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <Breadcrumbs items={[
        { label: 'ホーム', href: '/' },
        { label: 'コンプライアンス' },
      ]} />

      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Icons.Shield />
            コンプライアンス管理
          </h1>
          <p className="text-gray-600 mt-2">
            労働者派遣法第26条準拠状況の監査と管理
          </p>
        </div>
        <button
          onClick={() => auditMutation.mutate()}
          disabled={auditMutation.isPending}
          className="btn btn-primary flex items-center gap-2"
        >
          {auditMutation.isPending ? (
            <>
              <span className="animate-spin">
                <Icons.Refresh />
              </span>
              監査中...
            </>
          ) : (
            <>
              <Icons.Play />
              監査を実行
            </>
          )}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {[
          { id: 'overview', label: '概要' },
          { id: 'violations', label: '違反事項', count: latestReport?.summary?.violations_count },
          { id: 'alerts', label: 'アラート', count: alertsData?.summary?.critical + alertsData?.summary?.high },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Score and Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Compliance Score */}
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                コンプライアンススコア
              </h2>
              {isLoadingCompliance ? (
                <div className="h-32 bg-gray-100 rounded animate-pulse" />
              ) : (
                <ComplianceScore score={complianceData?.compliance?.score || 0} />
              )}
            </div>

            {/* Severity Summary */}
            <div className="card p-6 lg:col-span-2">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                重要度別件数
              </h2>
              {isLoadingAlerts ? (
                <div className="h-20 bg-gray-100 rounded animate-pulse" />
              ) : (
                <div className="flex flex-wrap gap-4">
                  <SeverityBadge severity="critical" count={alertsData?.summary?.critical || 0} />
                  <SeverityBadge severity="high" count={alertsData?.summary?.high || 0} />
                  <SeverityBadge severity="medium" count={alertsData?.summary?.medium || 0} />
                  <SeverityBadge severity="low" count={alertsData?.summary?.low || 0} />
                </div>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4 text-center">
              <p className="text-3xl font-bold text-gray-900">
                {complianceData?.compliance?.active_contracts || 0}
              </p>
              <p className="text-sm text-gray-500 mt-1">有効契約</p>
            </div>
            <div className="card p-4 text-center bg-red-50">
              <p className="text-3xl font-bold text-red-600">
                {complianceData?.compliance?.expired_but_active || 0}
              </p>
              <p className="text-sm text-gray-500 mt-1">期限切れ（要対応）</p>
            </div>
            <div className="card p-4 text-center bg-amber-50">
              <p className="text-3xl font-bold text-amber-600">
                {complianceData?.compliance?.factories_missing_info || 0}
              </p>
              <p className="text-sm text-gray-500 mt-1">工場情報不足</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">
                {latestReport?.contracts?.audited || '-'}
              </p>
              <p className="text-sm text-gray-500 mt-1">監査済み契約</p>
            </div>
          </div>

          {/* Last Audit Info */}
          {latestReport && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                最新監査レポート
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm text-gray-500">レポートID</p>
                  <p className="font-mono text-sm mt-1">{latestReport.report_id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">生成日時</p>
                  <p className="mt-1">{new Date(latestReport.generated_at).toLocaleString('ja-JP')}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">契約準拠率</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {latestReport.contracts?.compliance_rate || 100}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">工場準拠率</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {latestReport.factories?.compliance_rate || 100}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Top Priorities */}
          {complianceData?.top_priorities && complianceData.top_priorities.length > 0 && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                優先対応事項
              </h2>
              <div className="space-y-3">
                {complianceData.top_priorities.slice(0, 5).map((alert, idx) => (
                  <AlertCard key={idx} alert={alert} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Violations Tab */}
      {activeTab === 'violations' && (
        <div className="space-y-6">
          {!latestReport ? (
            <div className="card p-12 text-center">
              <Icons.ExclamationCircle />
              <p className="text-gray-500 mt-4">
                監査を実行すると違反事項が表示されます
              </p>
              <button
                onClick={() => auditMutation.mutate()}
                disabled={auditMutation.isPending}
                className="btn btn-primary mt-4"
              >
                監査を実行
              </button>
            </div>
          ) : (
            <>
              {/* Severity Filter */}
              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedSeverity(null)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    !selectedSeverity
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  すべて ({latestReport.violations.length + latestReport.warnings.length})
                </button>
                {['critical', 'high', 'medium', 'low'].map(severity => {
                  const count = [...latestReport.violations, ...latestReport.warnings].filter(
                    v => v.severity === severity
                  ).length
                  if (count === 0) return null
                  const colors: Record<string, string> = {
                    critical: 'bg-red-100 text-red-700',
                    high: 'bg-orange-100 text-orange-700',
                    medium: 'bg-amber-100 text-amber-700',
                    low: 'bg-blue-100 text-blue-700',
                  }
                  return (
                    <button
                      key={severity}
                      onClick={() => setSelectedSeverity(severity)}
                      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                        selectedSeverity === severity
                          ? colors[severity]
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {severity === 'critical' ? '緊急' :
                       severity === 'high' ? '高' :
                       severity === 'medium' ? '中' : '低'} ({count})
                    </button>
                  )
                })}
              </div>

              {/* Violations List */}
              {filteredViolations.length > 0 && (
                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-red-700 mb-4 flex items-center gap-2">
                    <Icons.Warning />
                    違反事項 ({filteredViolations.length})
                  </h2>
                  <div className="space-y-3">
                    {filteredViolations.map((violation, idx) => (
                      <ViolationCard key={idx} violation={violation} />
                    ))}
                  </div>
                </div>
              )}

              {/* Warnings List */}
              {filteredWarnings.length > 0 && (
                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-amber-700 mb-4 flex items-center gap-2">
                    <Icons.Warning />
                    警告 ({filteredWarnings.length})
                  </h2>
                  <div className="space-y-3">
                    {filteredWarnings.map((warning, idx) => (
                      <ViolationCard key={idx} violation={warning} />
                    ))}
                  </div>
                </div>
              )}

              {/* All Clear */}
              {filteredViolations.length === 0 && filteredWarnings.length === 0 && (
                <div className="card p-12 text-center bg-emerald-50">
                  <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto text-emerald-600">
                    <Icons.Check />
                  </div>
                  <p className="text-emerald-700 font-medium mt-4">
                    {selectedSeverity ? 'この重要度の違反はありません' : 'すべて準拠しています'}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {isLoadingAlerts ? (
            <div className="card p-6">
              <div className="h-40 bg-gray-100 rounded animate-pulse" />
            </div>
          ) : (
            <>
              {/* Critical Alerts */}
              {alertsData?.critical && alertsData.critical.length > 0 && (
                <div className="card p-6 border-red-200">
                  <h2 className="text-lg font-semibold text-red-700 mb-4">
                    緊急アラート ({alertsData.critical.length})
                  </h2>
                  <div className="space-y-3">
                    {alertsData.critical.map((alert, idx) => (
                      <AlertCard key={idx} alert={alert} />
                    ))}
                  </div>
                </div>
              )}

              {/* High Priority Alerts */}
              {alertsData?.high && alertsData.high.length > 0 && (
                <div className="card p-6 border-orange-200">
                  <h2 className="text-lg font-semibold text-orange-700 mb-4">
                    高優先度アラート ({alertsData.high.length})
                  </h2>
                  <div className="space-y-3">
                    {alertsData.high.map((alert, idx) => (
                      <AlertCard key={idx} alert={alert} />
                    ))}
                  </div>
                </div>
              )}

              {/* Medium Priority Alerts */}
              {alertsData?.medium && alertsData.medium.length > 0 && (
                <div className="card p-6 border-amber-200">
                  <h2 className="text-lg font-semibold text-amber-700 mb-4">
                    中優先度アラート ({alertsData.medium.length})
                  </h2>
                  <div className="space-y-3">
                    {alertsData.medium.map((alert, idx) => (
                      <AlertCard key={idx} alert={alert} />
                    ))}
                  </div>
                </div>
              )}

              {/* Low Priority Alerts */}
              {alertsData?.low && alertsData.low.length > 0 && (
                <div className="card p-6 border-blue-200">
                  <h2 className="text-lg font-semibold text-blue-700 mb-4">
                    低優先度アラート ({alertsData.low.length})
                  </h2>
                  <div className="space-y-3">
                    {alertsData.low.map((alert, idx) => (
                      <AlertCard key={idx} alert={alert} />
                    ))}
                  </div>
                </div>
              )}

              {/* No Alerts */}
              {(!alertsData?.critical?.length && !alertsData?.high?.length &&
                !alertsData?.medium?.length && !alertsData?.low?.length) && (
                <div className="card p-12 text-center bg-emerald-50">
                  <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto text-emerald-600">
                    <Icons.Check />
                  </div>
                  <p className="text-emerald-700 font-medium mt-4">
                    アラートはありません
                  </p>
                  <p className="text-emerald-600 text-sm mt-2">
                    すべてのシステムが正常に動作しています
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
