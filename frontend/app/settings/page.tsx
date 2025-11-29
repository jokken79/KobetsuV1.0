'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi, UNSFormDefaults } from '@/lib/api'

const WORK_DAYS = ['月', '火', '水', '木', '金', '土', '日']
const RESPONSIBILITY_LEVELS = ['補助的業務', '通常業務', '責任業務']

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<UNSFormDefaults | null>(null)
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Fetch current settings
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['form-defaults'],
    queryFn: settingsApi.getFormDefaults,
  })

  // Update form data when settings are loaded
  useEffect(() => {
    if (settings) {
      setFormData(settings)
    }
  }, [settings])

  // Mutation to save settings
  const saveMutation = useMutation({
    mutationFn: settingsApi.updateFormDefaults,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-defaults'] })
      setSaveMessage({ type: 'success', text: '設定を保存しました' })
      setTimeout(() => setSaveMessage(null), 3000)
    },
    onError: (error: any) => {
      setSaveMessage({
        type: 'error',
        text: error.response?.data?.detail || '保存に失敗しました'
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (formData) {
      saveMutation.mutate(formData)
    }
  }

  const updateComplaintContact = (field: string, value: string) => {
    if (!formData) return
    setFormData({
      ...formData,
      complaint_contact: {
        ...formData.complaint_contact,
        [field]: value,
      },
    })
  }

  const updateManager = (field: string, value: string) => {
    if (!formData) return
    setFormData({
      ...formData,
      manager: {
        ...formData.manager,
        [field]: value,
      },
    })
  }

  const updateWorkConditions = (field: string, value: string | number | string[]) => {
    if (!formData) return
    setFormData({
      ...formData,
      work_conditions: {
        ...formData.work_conditions,
        [field]: value,
      },
    })
  }

  const toggleWorkDay = (day: string) => {
    if (!formData) return
    const currentDays = formData.work_conditions.work_days
    const newDays = currentDays.includes(day)
      ? currentDays.filter((d) => d !== day)
      : [...currentDays, day]
    updateWorkConditions('work_days', newDays)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
        設定の読み込みに失敗しました
      </div>
    )
  }

  if (!formData) return null

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            システム設定
          </h1>
          <p className="text-gray-500 mt-1">
            UNS企画の連絡先情報とデフォルト値を設定
          </p>
        </div>
      </div>

      {/* Save Message */}
      {saveMessage && (
        <div
          className={`px-4 py-3 rounded-md ${
            saveMessage.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-700'
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}
        >
          {saveMessage.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 派遣元苦情処理担当者 */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">
              派遣元苦情処理担当者
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              労働者派遣法第26条第1項第9号に基づく苦情処理担当者
            </p>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">部署 *</label>
                <input
                  type="text"
                  value={formData.complaint_contact.department}
                  onChange={(e) => updateComplaintContact('department', e.target.value)}
                  className="form-input"
                  placeholder="例: 管理部"
                />
              </div>
              <div>
                <label className="form-label">役職 *</label>
                <input
                  type="text"
                  value={formData.complaint_contact.position}
                  onChange={(e) => updateComplaintContact('position', e.target.value)}
                  className="form-input"
                  placeholder="例: 部長"
                />
              </div>
              <div>
                <label className="form-label">氏名 *</label>
                <input
                  type="text"
                  value={formData.complaint_contact.name}
                  onChange={(e) => updateComplaintContact('name', e.target.value)}
                  className="form-input"
                  placeholder="例: 山田太郎"
                />
              </div>
              <div>
                <label className="form-label">電話番号 *</label>
                <input
                  type="tel"
                  value={formData.complaint_contact.phone}
                  onChange={(e) => updateComplaintContact('phone', e.target.value)}
                  className="form-input"
                  placeholder="例: 052-123-4567"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 派遣元責任者 */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">
              派遣元責任者
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              労働者派遣法第36条に基づく派遣元責任者
            </p>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">部署 *</label>
                <input
                  type="text"
                  value={formData.manager.department}
                  onChange={(e) => updateManager('department', e.target.value)}
                  className="form-input"
                  placeholder="例: 派遣事業部"
                />
              </div>
              <div>
                <label className="form-label">役職 *</label>
                <input
                  type="text"
                  value={formData.manager.position}
                  onChange={(e) => updateManager('position', e.target.value)}
                  className="form-input"
                  placeholder="例: 部長"
                />
              </div>
              <div>
                <label className="form-label">氏名 *</label>
                <input
                  type="text"
                  value={formData.manager.name}
                  onChange={(e) => updateManager('name', e.target.value)}
                  className="form-input"
                  placeholder="例: 鈴木一郎"
                />
              </div>
              <div>
                <label className="form-label">電話番号 *</label>
                <input
                  type="tel"
                  value={formData.manager.phone}
                  onChange={(e) => updateManager('phone', e.target.value)}
                  className="form-input"
                  placeholder="例: 052-123-4568"
                />
              </div>
              <div className="md:col-span-2">
                <label className="form-label">派遣元責任者講習修了証番号</label>
                <input
                  type="text"
                  value={formData.manager.license_number || ''}
                  onChange={(e) => updateManager('license_number', e.target.value)}
                  className="form-input"
                  placeholder="例: R5-12345（任意）"
                />
              </div>
            </div>
          </div>
        </div>

        {/* デフォルト就業条件 */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-gray-900">
              デフォルト就業条件
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              新規契約書作成時に自動入力される就業条件
            </p>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {/* Work Days */}
              <div>
                <label className="form-label">就業日</label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {WORK_DAYS.map((day) => (
                    <button
                      key={day}
                      type="button"
                      onClick={() => toggleWorkDay(day)}
                      className={`px-4 py-2 rounded-md font-medium transition-colors ${
                        formData.work_conditions.work_days.includes(day)
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {day}
                    </button>
                  ))}
                </div>
              </div>

              {/* Work Hours */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">始業時刻</label>
                  <input
                    type="time"
                    value={formData.work_conditions.work_start_time}
                    onChange={(e) => updateWorkConditions('work_start_time', e.target.value)}
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="form-label">終業時刻</label>
                  <input
                    type="time"
                    value={formData.work_conditions.work_end_time}
                    onChange={(e) => updateWorkConditions('work_end_time', e.target.value)}
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="form-label">休憩時間（分）</label>
                  <input
                    type="number"
                    value={formData.work_conditions.break_time_minutes}
                    onChange={(e) => updateWorkConditions('break_time_minutes', parseInt(e.target.value) || 0)}
                    className="form-input"
                    min="0"
                    max="180"
                  />
                </div>
              </div>

              {/* Rates */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">基本時間単価（円）</label>
                  <input
                    type="number"
                    value={formData.work_conditions.hourly_rate}
                    onChange={(e) => updateWorkConditions('hourly_rate', parseInt(e.target.value) || 0)}
                    className="form-input"
                    min="800"
                    max="10000"
                  />
                </div>
                <div>
                  <label className="form-label">時間外単価（円）</label>
                  <input
                    type="number"
                    value={formData.work_conditions.overtime_rate}
                    onChange={(e) => updateWorkConditions('overtime_rate', parseInt(e.target.value) || 0)}
                    className="form-input"
                    min="1000"
                    max="15000"
                  />
                </div>
                <div>
                  <label className="form-label">責任の程度</label>
                  <select
                    value={formData.work_conditions.responsibility_level}
                    onChange={(e) => updateWorkConditions('responsibility_level', e.target.value)}
                    className="form-select"
                  >
                    {RESPONSIBILITY_LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="btn-primary px-6 py-2"
          >
            {saveMutation.isPending ? '保存中...' : '設定を保存'}
          </button>
        </div>
      </form>
    </div>
  )
}
