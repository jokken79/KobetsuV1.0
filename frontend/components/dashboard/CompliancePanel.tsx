'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { complianceApi, AlertItem } from '@/lib/api'

interface CompliancePanelProps {
  className?: string
}

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
  Bell: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  ),
  Check: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  ArrowRight: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
    </svg>
  ),
}

function ComplianceScore({ score, status }: { score: number; status: string }) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-600'
    if (score >= 70) return 'text-amber-600'
    return 'text-red-600'
  }

  const getScoreBg = (score: number) => {
    if (score >= 90) return 'bg-emerald-100'
    if (score >= 70) return 'bg-amber-100'
    return 'bg-red-100'
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'COMPLIANT': return '準拠'
      case 'ISSUES_FOUND': return '要対応'
      default: return '不明'
    }
  }

  return (
    <div className="flex items-center gap-4">
      <div className={`relative w-20 h-20 rounded-full ${getScoreBg(score)} flex items-center justify-center`}>
        <span className={`text-2xl font-bold ${getScoreColor(score)}`}>{score}</span>
        <span className={`absolute -bottom-1 text-xs font-medium ${getScoreColor(score)}`}>点</span>
      </div>
      <div>
        <p className={`text-sm font-medium ${getScoreColor(score)}`}>
          {getStatusLabel(status)}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          労働者派遣法第26条
        </p>
      </div>
    </div>
  )
}

function AlertBadge({ priority, count }: { priority: string; count: number }) {
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

  if (count === 0) return null

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${styles[priority] || styles.low}`}>
      {labels[priority]}: {count}
    </span>
  )
}

function AlertListItem({ alert }: { alert: AlertItem }) {
  const priorityColors: Record<string, string> = {
    critical: 'border-l-red-500 bg-red-50',
    high: 'border-l-orange-500 bg-orange-50',
    medium: 'border-l-amber-500 bg-amber-50',
    low: 'border-l-blue-500 bg-blue-50',
  }

  return (
    <Link
      href={alert.action_url}
      className={`block p-3 border-l-4 ${priorityColors[alert.priority] || priorityColors.low} rounded-r-lg hover:shadow-md transition-shadow`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-medium text-gray-900 text-sm truncate">
            {alert.title}
          </p>
          <p className="text-xs text-gray-600 mt-0.5 truncate">
            {alert.message}
          </p>
        </div>
        {alert.expires_in_days !== undefined && (
          <span className="text-xs text-gray-500 flex-shrink-0">
            {alert.expires_in_days > 0 ? `${alert.expires_in_days}日` : '期限切れ'}
          </span>
        )}
      </div>
    </Link>
  )
}

export function CompliancePanel({ className = '' }: CompliancePanelProps) {
  const { data: complianceData, isLoading, error } = useQuery({
    queryKey: ['compliance-stats'],
    queryFn: () => complianceApi.getCompliance(),
    refetchInterval: 60000, // Refresh every minute
  })

  if (isLoading) {
    return (
      <div className={`card ${className}`}>
        <div className="card-header">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gray-100 animate-pulse" />
            <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            <div className="h-20 bg-gray-100 rounded animate-pulse" />
            <div className="h-24 bg-gray-100 rounded animate-pulse" />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`card ${className}`}>
        <div className="card-body">
          <div className="text-center py-6">
            <p className="text-red-600">コンプライアンスデータの取得に失敗しました</p>
          </div>
        </div>
      </div>
    )
  }

  const { compliance, alerts, top_priorities = [] } = complianceData || {}

  return (
    <div className={`card ${className}`}>
      <div className="card-header flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600">
            <Icons.Shield />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              コンプライアンス
            </h2>
            <p className="text-sm text-gray-500">法令準拠状況</p>
          </div>
        </div>
        <Link
          href="/compliance"
          className="btn btn-sm btn-ghost group"
        >
          詳細
          <span className="group-hover:translate-x-1 transition-transform">
            <Icons.ArrowRight />
          </span>
        </Link>
      </div>

      <div className="card-body space-y-6">
        {/* Compliance Score */}
        <div className="flex items-center justify-between">
          <ComplianceScore
            score={compliance?.score || 0}
            status={compliance?.status || 'UNKNOWN'}
          />

          {/* Alert Summary */}
          <div className="flex flex-col gap-2 items-end">
            <div className="flex gap-2 flex-wrap justify-end">
              <AlertBadge priority="critical" count={alerts?.critical || 0} />
              <AlertBadge priority="high" count={alerts?.high || 0} />
            </div>
            {alerts?.total_action_required > 0 && (
              <p className="text-xs text-gray-500">
                {alerts.total_action_required}件の対応が必要
              </p>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">
              {compliance?.active_contracts || 0}
            </p>
            <p className="text-xs text-gray-500">有効契約</p>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">
              {compliance?.expired_but_active || 0}
            </p>
            <p className="text-xs text-gray-500">期限切れ</p>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-lg">
            <p className="text-2xl font-bold text-amber-600">
              {compliance?.factories_missing_info || 0}
            </p>
            <p className="text-xs text-gray-500">要補完</p>
          </div>
        </div>

        {/* Priority Alerts */}
        {top_priorities.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <Icons.Bell />
              優先アラート
            </h3>
            <div className="space-y-2">
              {top_priorities.slice(0, 3).map((alert, idx) => (
                <AlertListItem key={idx} alert={alert} />
              ))}
            </div>
          </div>
        )}

        {/* All Good State */}
        {top_priorities.length === 0 && (compliance?.score || 0) >= 90 && (
          <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-lg">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
              <Icons.Check />
            </div>
            <div>
              <p className="font-medium text-emerald-700">すべて順調です</p>
              <p className="text-sm text-emerald-600">対応が必要なアラートはありません</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CompliancePanel
