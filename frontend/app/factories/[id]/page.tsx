'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { factoryApi } from '@/lib/api'
import type { FactoryUpdate } from '@/types'

export default function EditFactoryPage() {
  const router = useRouter()
  const params = useParams()
  const queryClient = useQueryClient()
  const factoryId = parseInt(params.id as string)

  const [formData, setFormData] = useState<Partial<FactoryUpdate>>({})
  const [isEditing, setIsEditing] = useState(false)

  // Fetch factory data
  const { data: factory, isLoading } = useQuery({
    queryKey: ['factory', factoryId],
    queryFn: () => factoryApi.getById(factoryId),
  })

  // Update formData when factory data loads
  useEffect(() => {
    if (factory) {
      setFormData({
        company_name: factory.company_name,
        company_address: factory.company_address,
        company_phone: factory.company_phone,
        company_fax: factory.company_fax,
        client_responsible_department: factory.client_responsible_department,
        client_responsible_name: factory.client_responsible_name,
        client_responsible_phone: factory.client_responsible_phone,
        plant_name: factory.plant_name,
        plant_address: factory.plant_address,
        plant_phone: factory.plant_phone,
        work_hours_description: factory.work_hours_description,
        break_minutes: factory.break_minutes,
        conflict_date: factory.conflict_date,
        is_active: factory.is_active,
        notes: factory.notes,
      })
    }
  }, [factory])

  const updateMutation = useMutation({
    mutationFn: (data: FactoryUpdate) => factoryApi.update(factoryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory', factoryId] })
      queryClient.invalidateQueries({ queryKey: ['factories'] })
      alert('工場情報を更新しました')
      setIsEditing(false)
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => factoryApi.delete(factoryId),
    onSuccess: () => {
      alert('工場を削除しました（無効に変更）')
      router.push('/factories')
    },
    onError: (error: any) => {
      alert(`エラー: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData as FactoryUpdate)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : undefined) : value
    }))
  }

  const handleDelete = () => {
    if (confirm('本当にこの工場を削除しますか？（無効に変更されます）')) {
      deleteMutation.mutate()
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 mt-4">読み込み中...</p>
        </div>
      </div>
    )
  }

  if (!factory) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600">工場が見つかりません</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">工場情報</h1>
            <p className="text-gray-600 mt-2">
              {factory.company_name} - {factory.plant_name}
            </p>
          </div>
          <div className="flex gap-3">
            {!isEditing ? (
              <>
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  編集
                </button>
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  戻る
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false)
                  // Reset form data
                  if (factory) {
                    setFormData({
                      company_name: factory.company_name,
                      plant_name: factory.plant_name,
                      // ... other fields
                    })
                  }
                }}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                キャンセル
              </button>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          {/* Company Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              企業情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  派遣先企業名
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  企業住所
                </label>
                <input
                  type="text"
                  name="company_address"
                  value={formData.company_address || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  企業電話番号
                </label>
                <input
                  type="tel"
                  name="company_phone"
                  value={formData.company_phone || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  FAX番号
                </label>
                <input
                  type="tel"
                  name="company_fax"
                  value={formData.company_fax || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Plant Info */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              工場情報
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  工場名
                </label>
                <input
                  type="text"
                  name="plant_name"
                  value={formData.plant_name || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  工場住所
                </label>
                <input
                  type="text"
                  name="plant_address"
                  value={formData.plant_address || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  工場電話番号
                </label>
                <input
                  type="tel"
                  name="plant_phone"
                  value={formData.plant_phone || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Responsible Person */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              派遣先責任者
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  部署名
                </label>
                <input
                  type="text"
                  name="client_responsible_department"
                  value={formData.client_responsible_department || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  担当者名
                </label>
                <input
                  type="text"
                  name="client_responsible_name"
                  value={formData.client_responsible_name || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  連絡先電話番号
                </label>
                <input
                  type="tel"
                  name="client_responsible_phone"
                  value={formData.client_responsible_phone || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Work Schedule */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
              就業スケジュール
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  就業時間説明
                </label>
                <textarea
                  name="work_hours_description"
                  value={formData.work_hours_description || ''}
                  onChange={handleChange}
                  rows={3}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  休憩時間（分）
                </label>
                <input
                  type="number"
                  name="break_minutes"
                  value={formData.break_minutes || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  抵触日
                </label>
                <input
                  type="date"
                  name="conflict_date"
                  value={formData.conflict_date || ''}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              備考
            </label>
            <textarea
              name="notes"
              value={formData.notes || ''}
              onChange={handleChange}
              rows={4}
              disabled={!isEditing}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            />
          </div>

          {/* Actions */}
          {isEditing && (
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-gray-400"
              >
                削除
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
              >
                {updateMutation.isPending ? '更新中...' : '保存'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
