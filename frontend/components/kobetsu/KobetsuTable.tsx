'use client'

import Link from 'next/link'
import { StatusBadge } from './StatusBadge'
import type { KobetsuListItem } from '@/types'

interface KobetsuTableProps {
  contracts: KobetsuListItem[]
  compact?: boolean
}

export function KobetsuTable({ contracts, compact = false }: KobetsuTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="table">
        <thead>
          <tr>
            <th>契約番号</th>
            <th>派遣先</th>
            {!compact && <th>期間</th>}
            <th>労働者数</th>
            <th>ステータス</th>
            {!compact && <th>作成日</th>}
            <th></th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {contracts.map((contract) => (
            <tr key={contract.id}>
              <td>
                <Link
                  href={`/kobetsu/${contract.id}`}
                  className="font-medium text-primary-600 hover:text-primary-700"
                >
                  {contract.contract_number}
                </Link>
              </td>
              <td>
                <div className="max-w-xs truncate" title={contract.worksite_name}>
                  {contract.worksite_name}
                </div>
              </td>
              {!compact && (
                <td>
                  <div className="text-sm">
                    {new Date(contract.dispatch_start_date).toLocaleDateString('ja-JP')}
                    <span className="text-gray-400 mx-1">〜</span>
                    {new Date(contract.dispatch_end_date).toLocaleDateString('ja-JP')}
                  </div>
                </td>
              )}
              <td>
                <span className="font-medium">{contract.number_of_workers}</span>
                <span className="text-gray-500 text-sm">名</span>
              </td>
              <td>
                <StatusBadge status={contract.status} />
              </td>
              {!compact && (
                <td className="text-sm text-gray-500">
                  {new Date(contract.created_at).toLocaleDateString('ja-JP')}
                </td>
              )}
              <td>
                <Link
                  href={`/kobetsu/${contract.id}`}
                  className="text-gray-400 hover:text-gray-600"
                >
                  →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
