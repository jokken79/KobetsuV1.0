'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { kobetsuApi } from '@/lib/api'
import { KobetsuForm } from '@/components/kobetsu/KobetsuForm'
import type { KobetsuCreate, KobetsuUpdate } from '@/types'

export default function EditKobetsuPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const id = Number(params.id)
  const [error, setError] = useState<string | null>(null)

  // Fetch existing contract data
  const { data: contract, isLoading: contractLoading } = useQuery({
    queryKey: ['kobetsu', id],
    queryFn: () => kobetsuApi.getById(id),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: KobetsuUpdate) => kobetsuApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu', id] })
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
      router.push(`/kobetsu/${id}`)
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Error occurred while updating')
    },
  })

  const handleSubmit = (data: KobetsuCreate) => {
    setError(null)
    // Convert to update format (only changed fields)
    const updateData: KobetsuUpdate = {
      contract_date: data.contract_date,
      dispatch_end_date: data.dispatch_end_date,
      work_content: data.work_content,
      responsibility_level: data.responsibility_level,
      supervisor_name: data.supervisor_name,
      work_days: data.work_days,
      hourly_rate: data.hourly_rate,
      overtime_rate: data.overtime_rate,
    }
    updateMutation.mutate(updateData)
  }

  if (contractLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-8 h-8"></div>
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Contract not found</p>
        <Link href="/kobetsu" className="btn-primary">
          Back to list
        </Link>
      </div>
    )
  }

  // Only draft contracts can be edited
  if (contract.status !== 'draft') {
    return (
      <div className="text-center py-12">
        <p className="text-yellow-600 mb-4">Only draft contracts can be edited</p>
        <Link href={`/kobetsu/${id}`} className="btn-primary">
          Back to contract
        </Link>
      </div>
    )
  }

  // Convert contract to form initial data
  const initialData: Partial<KobetsuCreate> = {
    factory_id: contract.factory_id,
    employee_ids: [],
    contract_date: contract.contract_date,
    dispatch_start_date: contract.dispatch_start_date,
    dispatch_end_date: contract.dispatch_end_date,
    work_content: contract.work_content,
    responsibility_level: contract.responsibility_level,
    worksite_name: contract.worksite_name,
    worksite_address: contract.worksite_address,
    organizational_unit: contract.organizational_unit || '',
    supervisor_department: contract.supervisor_department,
    supervisor_position: contract.supervisor_position,
    supervisor_name: contract.supervisor_name,
    work_days: contract.work_days,
    work_start_time: contract.work_start_time,
    work_end_time: contract.work_end_time,
    break_time_minutes: contract.break_time_minutes,
    hourly_rate: Number(contract.hourly_rate),
    overtime_rate: Number(contract.overtime_rate),
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Edit Contract: {contract.contract_number}
          </h1>
          <p className="text-gray-500 mt-1">
            {contract.worksite_name}
          </p>
        </div>
        <Link href={`/kobetsu/${id}`} className="btn-secondary">
          Cancel
        </Link>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Form */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">
            Edit Contract Information
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            * Required fields
          </p>
        </div>
        <div className="card-body">
          <KobetsuForm
            initialData={initialData}
            onSubmit={handleSubmit}
            isLoading={updateMutation.isPending}
          />
        </div>
      </div>
    </div>
  )
}
