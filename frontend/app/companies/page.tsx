'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import axios from 'axios'
import type { CompanyShiftResponse, CompanyShiftCreate, CompanyShiftUpdate } from '@/types'

interface Company {
  company_id: number
  name: string
  name_kana?: string
  address?: string
  phone?: string
  is_active: boolean
  shifts?: CompanyShiftResponse[]
}

export default function CompaniesPage() {
  const router = useRouter()
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const [showShiftModal, setShowShiftModal] = useState(false)
  const [editingShift, setEditingShift] = useState<CompanyShiftResponse | null>(null)

  // Fetch companies
  useEffect(() => {
    fetchCompanies()
  }, [])

  const fetchCompanies = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/companies`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCompanies(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching companies:', err)
      setError('企業の読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }

  // Fetch shifts for a company
  const fetchCompanyShifts = async (companyId: number) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/companies/${companyId}/shifts`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Update company shifts in state
      setCompanies(prev => prev.map(c =>
        c.company_id === companyId ? { ...c, shifts: response.data } : c
      ))
    } catch (err) {
      console.error('Error fetching shifts:', err)
    }
  }

  // Handle company selection
  const handleSelectCompany = async (company: Company) => {
    setSelectedCompany(company)
    if (!company.shifts) {
      await fetchCompanyShifts(company.company_id)
    }
  }

  // Open shift modal
  const openShiftModal = (shift?: CompanyShiftResponse) => {
    setEditingShift(shift || null)
    setShowShiftModal(true)
  }

  // Close shift modal
  const closeShiftModal = () => {
    setShowShiftModal(false)
    setEditingShift(null)
  }

  // Save shift (create or update)
  const saveShift = async (shiftData: CompanyShiftCreate | CompanyShiftUpdate) => {
    if (!selectedCompany) return

    try {
      const token = localStorage.getItem('access_token')
      const headers = { Authorization: `Bearer ${token}` }

      if (editingShift) {
        // Update existing shift
        await axios.put(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/companies/shifts/${editingShift.id}`,
          shiftData,
          { headers }
        )
      } else {
        // Create new shift
        await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/companies/${selectedCompany.company_id}/shifts`,
          shiftData,
          { headers }
        )
      }

      // Refresh shifts
      await fetchCompanyShifts(selectedCompany.company_id)
      closeShiftModal()
    } catch (err: any) {
      console.error('Error saving shift:', err)
      alert('シフトの保存に失敗しました')
    }
  }

  // Delete shift
  const deleteShift = async (shiftId: number) => {
    if (!selectedCompany) return
    if (!confirm('このシフトを削除してもよろしいですか？')) return

    try {
      const token = localStorage.getItem('access_token')
      await axios.delete(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/companies/shifts/${shiftId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Refresh shifts
      await fetchCompanyShifts(selectedCompany.company_id)
    } catch (err: any) {
      console.error('Error deleting shift:', err)
      alert('シフトの削除に失敗しました')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">読み込み中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">企業管理</h1>
          <p className="text-gray-600">企業ごとの共通シフト設定 - 全工場に継承されます</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Companies List */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">企業一覧 ({companies.length}件)</h2>

            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {companies.map((company) => (
                <div
                  key={company.company_id}
                  onClick={() => handleSelectCompany(company)}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedCompany?.company_id === company.company_id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{company.name}</h3>
                      {company.name_kana && (
                        <p className="text-sm text-gray-500">{company.name_kana}</p>
                      )}
                    </div>
                    <div className="text-sm">
                      <span className="bg-indigo-100 text-indigo-800 px-2 py-1 rounded">
                        {company.shifts?.filter(s => s.is_active).length || 0} シフト
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Shift Management */}
          <div className="bg-white rounded-lg shadow p-6">
            {selectedCompany ? (
              <>
                <div className="mb-6">
                  <h2 className="text-xl font-bold mb-2">{selectedCompany.name}</h2>
                  <p className="text-sm text-gray-600">
                    この企業の全工場が以下のシフトを継承します
                  </p>
                </div>

                <div className="mb-4">
                  <button
                    onClick={() => openShiftModal()}
                    className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    + 新規シフト追加
                  </button>
                </div>

                <div className="space-y-3">
                  {selectedCompany.shifts && selectedCompany.shifts.length > 0 ? (
                    selectedCompany.shifts
                      .filter(s => s.is_active)
                      .sort((a, b) => a.display_order - b.display_order)
                      .map((shift) => (
                        <div
                          key={shift.id}
                          className="border border-indigo-200 rounded-lg p-4 bg-indigo-50"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="font-bold text-indigo-900">{shift.shift_name}</h3>
                              {shift.shift_start && shift.shift_end && (
                                <p className="text-sm text-indigo-700 mt-1">
                                  🕐 {shift.shift_start.substring(0, 5)} - {shift.shift_end.substring(0, 5)}
                                </p>
                              )}
                              {shift.shift_premium && (
                                <p className="text-sm text-green-700 mt-1">
                                  💰 手当: ¥{shift.shift_premium.toLocaleString()}
                                  {shift.shift_premium_type && ` (${shift.shift_premium_type})`}
                                </p>
                              )}
                              {shift.description && (
                                <p className="text-xs text-gray-600 mt-1">{shift.description}</p>
                              )}
                            </div>
                            <div className="flex gap-2 ml-4">
                              <button
                                onClick={() => openShiftModal(shift)}
                                className="text-indigo-600 hover:text-indigo-800 text-sm"
                              >
                                編集
                              </button>
                              <button
                                onClick={() => deleteShift(shift.id)}
                                className="text-red-600 hover:text-red-800 text-sm"
                              >
                                削除
                              </button>
                            </div>
                          </div>
                        </div>
                      ))
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      シフトが登録されていません
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                左から企業を選択してください
              </div>
            )}
          </div>
        </div>

        {/* Shift Modal */}
        {showShiftModal && (
          <ShiftModal
            shift={editingShift}
            onSave={saveShift}
            onClose={closeShiftModal}
          />
        )}
      </div>
    </div>
  )
}

// Shift Modal Component
function ShiftModal({
  shift,
  onSave,
  onClose,
}: {
  shift: CompanyShiftResponse | null
  onSave: (data: CompanyShiftCreate | CompanyShiftUpdate) => void
  onClose: () => void
}) {
  const [formData, setFormData] = useState({
    shift_name: shift?.shift_name || '',
    shift_start: shift?.shift_start?.substring(0, 5) || '',
    shift_end: shift?.shift_end?.substring(0, 5) || '',
    shift_premium: shift?.shift_premium || '',
    shift_premium_type: shift?.shift_premium_type || '時給',
    description: shift?.description || '',
    display_order: shift?.display_order || 0,
    is_active: shift?.is_active ?? true,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      ...formData,
      shift_premium: formData.shift_premium ? Number(formData.shift_premium) : undefined,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6">
            {shift ? 'シフト編集' : '新規シフト追加'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                シフト名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.shift_name}
                onChange={(e) => setFormData({ ...formData, shift_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="例: 昼勤, 夜勤, 第3シフト"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  開始時間
                </label>
                <input
                  type="time"
                  value={formData.shift_start}
                  onChange={(e) => setFormData({ ...formData, shift_start: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  終了時間
                </label>
                <input
                  type="time"
                  value={formData.shift_end}
                  onChange={(e) => setFormData({ ...formData, shift_end: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  手当金額（円）
                </label>
                <input
                  type="number"
                  value={formData.shift_premium}
                  onChange={(e) => setFormData({ ...formData, shift_premium: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="0"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  手当種別
                </label>
                <select
                  value={formData.shift_premium_type}
                  onChange={(e) => setFormData({ ...formData, shift_premium_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="時給">時給</option>
                  <option value="日給">日給</option>
                  <option value="月額">月額</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                説明・備考
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={3}
                placeholder="このシフトの詳細説明"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  表示順序
                </label>
                <input
                  type="number"
                  value={formData.display_order}
                  onChange={(e) => setFormData({ ...formData, display_order: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  min="0"
                />
              </div>
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">有効</span>
                </label>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                保存
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                キャンセル
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
