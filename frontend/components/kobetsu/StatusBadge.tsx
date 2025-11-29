'use client'

interface StatusBadgeProps {
  status: string
}

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: {
    label: '下書き',
    className: 'badge-draft',
  },
  active: {
    label: '有効',
    className: 'badge-active',
  },
  expired: {
    label: '期限切れ',
    className: 'badge-expired',
  },
  cancelled: {
    label: 'キャンセル',
    className: 'badge-cancelled',
  },
  renewed: {
    label: '更新済み',
    className: 'badge-renewed',
  },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || {
    label: status,
    className: 'badge bg-gray-100 text-gray-800',
  }

  return (
    <span className={config.className}>
      {config.label}
    </span>
  )
}
