'use client'

import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { useConfirmActions } from '@/components/common/ConfirmContext'
import { SkeletonCard } from '@/components/common/Skeleton'
import { useToastActions } from '@/components/common/ToastContext'
import { FactoryTree } from '@/components/factory/FactoryTree'
import { LineCard } from '@/components/factory/LineCard'
import { ShiftEditModal } from '@/components/factory/ShiftEditModal'
import { BreakEditModal } from '@/components/factory/BreakEditModal'
import { useDeleteFactory, useUpdateFactory } from '@/hooks/useFactories'
import { employeeApi, factoryApi, importApi } from '@/lib/api'
import { formatBreakTimeForDisplay } from '@/lib/formatBreakTime'
import type {
  EmployeeResponse,
  FactoryLineResponse,
  FactoryUpdate,
  FactoryShiftResponse,
  FactoryBreakResponse
} from '@/types'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'

export default function FactoriesPage() {
  const router = useRouter()
  const [selectedFactoryId, setSelectedFactoryId] = useState<number | null>(null)
  const [isEditingFactory, setIsEditingFactory] = useState(false)
  const [factoryFormData, setFactoryFormData] = useState<FactoryUpdate>({})
  const [expandedLines, setExpandedLines] = useState<Set<number>>(new Set())
  const [isSyncing, setIsSyncing] = useState(false)
  const [showAllEmployees, setShowAllEmployees] = useState(false) // false = active only (default)

  // Modal states
  const [showShiftModal, setShowShiftModal] = useState(false)
  const [editingShift, setEditingShift] = useState<FactoryShiftResponse | null>(null)
  const [showBreakModal, setShowBreakModal] = useState(false)
  const [editingBreak, setEditingBreak] = useState<FactoryBreakResponse | null>(null)

  const toast = useToastActions()
  const { confirmDelete } = useConfirmActions()

  // Fetch all factories for tree
  const { data: factories = [], isLoading: isLoadingFactories } = useQuery({
    queryKey: ['factories', 'list'],
    queryFn: () => factoryApi.getList({ limit: 500 }),
    staleTime: 5 * 60 * 1000,
  })

  // Fetch selected factory details
  const { data: factoryDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['factories', selectedFactoryId],
    queryFn: () => selectedFactoryId ? factoryApi.getById(selectedFactoryId) : null,
    enabled: !!selectedFactoryId,
  })

  // Fetch employees for the selected factory
  const { data: employees = [], isLoading: isLoadingEmployees } = useQuery({
    queryKey: ['employees', 'by-factory', selectedFactoryId, showAllEmployees],
    queryFn: () => selectedFactoryId ? employeeApi.getList({
      factory_id: selectedFactoryId,
      limit: 500,
      status: showAllEmployees ? 'all' : 'active'
    }) : [],
    enabled: !!selectedFactoryId,
  })

  // Group employees by factory_line_id
  const employeesByLine = useMemo(() => {
    const grouped = new Map<number | null, EmployeeResponse[]>()
    employees.forEach(emp => {
      // Cast EmployeeListItem to EmployeeResponse for LineCard compatibility
      const empAsResponse = emp as unknown as EmployeeResponse
      const lineId = (emp as any).factory_line_id || null
      const existing = grouped.get(lineId) || []
      grouped.set(lineId, [...existing, empAsResponse])
    })
    return grouped
  }, [employees])

  // Group unassigned employees by their line_name and department
  const unassignedByLineName = useMemo(() => {
    const unassigned = employeesByLine.get(null) || []
    const grouped = new Map<string, EmployeeResponse[]>()

    unassigned.forEach(emp => {
      // Create a group key from department and line_name
      const dept = (emp as any).department || ''
      const lineName = (emp as any).line_name || ''
      const groupKey = dept && lineName ? `${dept} / ${lineName}` :
                       dept ? dept :
                       lineName ? lineName :
                       '未分類'

      const existing = grouped.get(groupKey) || []
      grouped.set(groupKey, [...existing, emp])
    })

    // Sort by group key and convert to array
    return Array.from(grouped.entries()).sort((a, b) => {
      // Put 未分類 at the end
      if (a[0] === '未分類') return 1
      if (b[0] === '未分類') return -1
      return a[0].localeCompare(b[0])
    })
  }, [employeesByLine])

  // Mutations
  const updateFactoryMutation = useUpdateFactory(selectedFactoryId!)
  const deleteFactoryMutation = useDeleteFactory()

  // Initialize form data when factory detail loads
  useEffect(() => {
    if (factoryDetail) {
      setFactoryFormData({
        company_name: factoryDetail.company_name,
        company_address: factoryDetail.company_address,
        company_phone: factoryDetail.company_phone,
        company_fax: factoryDetail.company_fax,
        plant_name: factoryDetail.plant_name,
        plant_address: factoryDetail.plant_address,
        plant_phone: factoryDetail.plant_phone,
        client_responsible_department: factoryDetail.client_responsible_department,
        client_responsible_position: factoryDetail.client_responsible_position,
        client_responsible_name: factoryDetail.client_responsible_name,
        client_responsible_phone: factoryDetail.client_responsible_phone,
        client_complaint_department: factoryDetail.client_complaint_department,
        client_complaint_position: factoryDetail.client_complaint_position,
        client_complaint_name: factoryDetail.client_complaint_name,
        client_complaint_phone: factoryDetail.client_complaint_phone,
        dispatch_responsible_department: factoryDetail.dispatch_responsible_department,
        dispatch_responsible_name: factoryDetail.dispatch_responsible_name,
        dispatch_responsible_phone: factoryDetail.dispatch_responsible_phone,
        dispatch_complaint_department: factoryDetail.dispatch_complaint_department,
        dispatch_complaint_name: factoryDetail.dispatch_complaint_name,
        dispatch_complaint_phone: factoryDetail.dispatch_complaint_phone,
        work_hours_description: factoryDetail.work_hours_description,
        break_time_description: factoryDetail.break_time_description,
        calendar_description: factoryDetail.calendar_description,
        day_shift_start: factoryDetail.day_shift_start,
        day_shift_end: factoryDetail.day_shift_end,
        night_shift_start: factoryDetail.night_shift_start,
        night_shift_end: factoryDetail.night_shift_end,
        break_minutes: factoryDetail.break_minutes,
        overtime_description: factoryDetail.overtime_description,
        overtime_max_hours_day: factoryDetail.overtime_max_hours_day,
        overtime_max_hours_month: factoryDetail.overtime_max_hours_month,
        overtime_max_hours_year: factoryDetail.overtime_max_hours_year,
        overtime_special_max_month: factoryDetail.overtime_special_max_month,
        overtime_special_count_year: factoryDetail.overtime_special_count_year,
        holiday_work_description: factoryDetail.holiday_work_description,
        holiday_work_max_days_month: factoryDetail.holiday_work_max_days_month,
        conflict_date: factoryDetail.conflict_date,
        contract_start_date: factoryDetail.contract_start_date,
        contract_end_date: factoryDetail.contract_end_date,
        contract_cycle_type: factoryDetail.contract_cycle_type,
        cycle_day_type: factoryDetail.cycle_day_type,
        fiscal_year_end_month: factoryDetail.fiscal_year_end_month,
        fiscal_year_end_day: factoryDetail.fiscal_year_end_day,
        contract_renewal_days_before: factoryDetail.contract_renewal_days_before,
        time_unit_minutes: factoryDetail.time_unit_minutes,
        closing_date: factoryDetail.closing_date,
        payment_date: factoryDetail.payment_date,
        bank_account: factoryDetail.bank_account,
        worker_closing_date: factoryDetail.worker_closing_date,
        worker_payment_date: factoryDetail.worker_payment_date,
        worker_calendar: factoryDetail.worker_calendar,
        agreement_period: factoryDetail.agreement_period,
        agreement_explainer: factoryDetail.agreement_explainer,
        is_active: factoryDetail.is_active,
        notes: factoryDetail.notes,
      })
    }
  }, [factoryDetail])

  // Auto-select first factory on load (optional)
  useEffect(() => {
    if (!selectedFactoryId && factories.length > 0) {
      setSelectedFactoryId(factories[0].id)
    }
  }, [factories, selectedFactoryId])

  const handleSelectFactory = (factoryId: number) => {
    setSelectedFactoryId(factoryId)
    setIsEditingFactory(false)
    setExpandedLines(new Set()) // Reset expanded lines
  }

  const handleCreateNew = () => {
    router.push('/factories/create')
  }

  const handleEditFactory = () => {
    setIsEditingFactory(true)
  }

  const handleCancelEditFactory = () => {
    setIsEditingFactory(false)
    // Reset form to original data
    if (factoryDetail) {
      setFactoryFormData({
        company_name: factoryDetail.company_name,
        company_address: factoryDetail.company_address,
        company_phone: factoryDetail.company_phone,
        company_fax: factoryDetail.company_fax,
        plant_name: factoryDetail.plant_name,
        plant_address: factoryDetail.plant_address,
        plant_phone: factoryDetail.plant_phone,
        client_responsible_department: factoryDetail.client_responsible_department,
        client_responsible_position: factoryDetail.client_responsible_position,
        client_responsible_name: factoryDetail.client_responsible_name,
        client_responsible_phone: factoryDetail.client_responsible_phone,
        client_complaint_department: factoryDetail.client_complaint_department,
        client_complaint_position: factoryDetail.client_complaint_position,
        client_complaint_name: factoryDetail.client_complaint_name,
        client_complaint_phone: factoryDetail.client_complaint_phone,
        dispatch_responsible_department: factoryDetail.dispatch_responsible_department,
        dispatch_responsible_name: factoryDetail.dispatch_responsible_name,
        dispatch_responsible_phone: factoryDetail.dispatch_responsible_phone,
        dispatch_complaint_department: factoryDetail.dispatch_complaint_department,
        dispatch_complaint_name: factoryDetail.dispatch_complaint_name,
        dispatch_complaint_phone: factoryDetail.dispatch_complaint_phone,
        work_hours_description: factoryDetail.work_hours_description,
        break_time_description: factoryDetail.break_time_description,
        calendar_description: factoryDetail.calendar_description,
        day_shift_start: factoryDetail.day_shift_start,
        day_shift_end: factoryDetail.day_shift_end,
        night_shift_start: factoryDetail.night_shift_start,
        night_shift_end: factoryDetail.night_shift_end,
        break_minutes: factoryDetail.break_minutes,
        overtime_description: factoryDetail.overtime_description,
        overtime_max_hours_day: factoryDetail.overtime_max_hours_day,
        overtime_max_hours_month: factoryDetail.overtime_max_hours_month,
        overtime_max_hours_year: factoryDetail.overtime_max_hours_year,
        overtime_special_max_month: factoryDetail.overtime_special_max_month,
        overtime_special_count_year: factoryDetail.overtime_special_count_year,
        holiday_work_description: factoryDetail.holiday_work_description,
        holiday_work_max_days_month: factoryDetail.holiday_work_max_days_month,
        conflict_date: factoryDetail.conflict_date,
        contract_start_date: factoryDetail.contract_start_date,
        contract_end_date: factoryDetail.contract_end_date,
        contract_cycle_type: factoryDetail.contract_cycle_type,
        cycle_day_type: factoryDetail.cycle_day_type,
        fiscal_year_end_month: factoryDetail.fiscal_year_end_month,
        fiscal_year_end_day: factoryDetail.fiscal_year_end_day,
        contract_renewal_days_before: factoryDetail.contract_renewal_days_before,
        time_unit_minutes: factoryDetail.time_unit_minutes,
        closing_date: factoryDetail.closing_date,
        payment_date: factoryDetail.payment_date,
        bank_account: factoryDetail.bank_account,
        worker_closing_date: factoryDetail.worker_closing_date,
        worker_payment_date: factoryDetail.worker_payment_date,
        worker_calendar: factoryDetail.worker_calendar,
        agreement_period: factoryDetail.agreement_period,
        agreement_explainer: factoryDetail.agreement_explainer,
        is_active: factoryDetail.is_active,
        notes: factoryDetail.notes,
      })
    }
  }

  const handleSaveFactory = async () => {
    if (!selectedFactoryId) return

    try {
      console.log('Saving factory with data:', factoryFormData)
      await updateFactoryMutation.mutateAsync(factoryFormData)
      toast.success('工場情報を更新しました')
      setIsEditingFactory(false)
    } catch (error: any) {
      console.error('Failed to update factory:', error)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
      toast.error(`更新に失敗しました: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDeleteFactory = async () => {
    if (!selectedFactoryId || !factoryDetail) return

    const confirmed = await confirmDelete(
      `${factoryDetail.company_name} - ${factoryDetail.plant_name}`
    )

    if (confirmed) {
      try {
        await deleteFactoryMutation.mutateAsync(selectedFactoryId)
        toast.success('工場を削除しました')
        setSelectedFactoryId(null)
      } catch (error) {
        console.error('Failed to delete factory:', error)
        toast.error('削除に失敗しました')
      }
    }
  }

  const handleFieldChange = (field: keyof FactoryUpdate, value: string | number) => {
    setFactoryFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleEditLine = (lineId: number) => {
    // Navigate to line edit page or open modal
    router.push(`/factories/lines/${lineId}/edit`)
  }

  const handleDeleteLine = async (lineId: number) => {
    const confirmed = await confirmDelete('このライン')
    if (!confirmed) return

    try {
      await factoryApi.deleteLine(lineId)
      toast.success('ラインを削除しました')
      // Refetch factory details to update lines
      window.location.reload() // Simple reload for now
    } catch (error) {
      console.error('Failed to delete line:', error)
      toast.error('ラインの削除に失敗しました')
    }
  }

  const toggleLineExpand = (lineId: number) => {
    const newExpanded = new Set(expandedLines)
    if (newExpanded.has(lineId)) {
      newExpanded.delete(lineId)
    } else {
      newExpanded.add(lineId)
    }
    setExpandedLines(newExpanded)
  }

  // Sync employees to factories from Excel
  const handleSyncEmployeesToFactories = async () => {
    setIsSyncing(true)
    try {
      const result = await importApi.syncEmployeesToFactories()
      if (result.success) {
        toast.success(`同期完了: 新規${result.linked_count}件, 更新${result.updated_count}件`)
        // Refresh data
        window.location.reload()
      } else {
        toast.error(`同期エラー: ${result.message}`)
        if (result.not_found_factories.length > 0) {
          console.warn('Factories not found:', result.not_found_factories)
        }
      }
    } catch (error: any) {
      console.error('Sync failed:', error)
      toast.error(`同期に失敗しました: ${error.message || '不明なエラー'}`)
    } finally {
      setIsSyncing(false)
    }
  }

  // Shift modal handlers
  const handleSaveShift = async (shiftData: any) => {
    if (!selectedFactoryId) return

    try {
      if (editingShift) {
        // Update existing shift
        await factoryApi.updateShift(editingShift.id, shiftData)
        toast.success('シフトを更新しました')
      } else {
        // Create new shift
        await factoryApi.createShift(selectedFactoryId, shiftData)
        toast.success('シフトを追加しました')
      }

      // Refresh factory details
      window.location.reload()
    } catch (error: any) {
      console.error('Failed to save shift:', error)
      toast.error(`シフトの保存に失敗しました: ${error.response?.data?.detail || error.message}`)
      throw error // Re-throw so modal can handle loading state
    }
  }

  // Break modal handlers
  const handleSaveBreak = async (breakData: any) => {
    if (!selectedFactoryId) return

    try {
      if (editingBreak) {
        // Update existing break
        await factoryApi.updateBreak(editingBreak.id, breakData)
        toast.success('休憩を更新しました')
      } else {
        // Create new break
        await factoryApi.createBreak(selectedFactoryId, breakData)
        toast.success('休憩を追加しました')
      }

      // Refresh factory details
      window.location.reload()
    } catch (error: any) {
      console.error('Failed to save break:', error)
      toast.error(`休憩の保存に失敗しました: ${error.response?.data?.detail || error.message}`)
      throw error // Re-throw so modal can handle loading state
    }
  }

  // Helper to format break time for display
  const getBreakTimeSummary = (breakTimeDescription?: string, breakMinutes?: number) => {
    if (!breakTimeDescription || breakTimeDescription.trim() === '') {
      return `${breakMinutes || 0}分`
    }
    const lines = formatBreakTimeForDisplay(breakTimeDescription)
    if (lines.length === 0) {
      return `${breakMinutes || 0}分`
    }
    // Take first line (shift) and first period as summary
    const firstLine = lines[0]
    if (firstLine.startsWith('【')) {
      // If we have shift, maybe show shift + first period
      const secondLine = lines[1] || ''
      const summary = secondLine ? `${firstLine} ${secondLine.trim()}` : firstLine
      return `${summary} (${breakMinutes || 0}分)`
    } else {
      // No shift, just show first line
      return `${firstLine} (${breakMinutes || 0}分)`
    }
  }

  // Empty state component
  const EmptyState = ({ message }: { message: string }) => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <p className="text-gray-500 text-lg">{message}</p>
      </div>
    </div>
  )

  // Check authentication status
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    setIsAuthenticated(!!token)
    console.log('Auth token present?', !!token)
  }, [])

  const handleLoginRedirect = () => {
    router.push('/login')
  }

  return (
    <>
      {/* Breadcrumbs */}
      <Breadcrumbs items={[
        { label: 'ダッシュボード', href: '/' },
        { label: '派遣先工場・ライン管理', href: '/factories' }
      ]} />

      {/* Sync Button - Prominent at top */}
      <div className="bg-white border-b border-indigo-100 px-4 py-3 mb-0 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-indigo-700 font-medium">社員台帳から社員と工場をリンク</span>
          </div>
          <button
            onClick={handleSyncEmployeesToFactories}
            disabled={isSyncing}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all shadow-sm ${
              isSyncing
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white hover:shadow-md'
            }`}
          >
            {isSyncing ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>同期中...</span>
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>社員・工場同期</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Authentication Warning */}
      {!isAuthenticated && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                編集機能を使用するにはログインが必要です。
                <button
                  onClick={handleLoginRedirect}
                  className="ml-2 underline font-medium text-yellow-700 hover:text-yellow-600"
                >
                  ログインページへ
                </button>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex h-[calc(100vh-120px)] bg-gray-50">
        {/* Left Panel - Factory Tree */}
        <FactoryTree
          factories={factories}
          selectedFactoryId={selectedFactoryId}
          onSelectFactory={handleSelectFactory}
          onCreateNew={handleCreateNew}
          isLoading={isLoadingFactories}
        />

        {/* Right Panel - Factory Details */}
        <div className="flex-1 overflow-y-auto bg-white">
          {selectedFactoryId && factoryDetail ? (
            <div className="p-6">
              {/* Factory Header */}
              <div className="border-b border-indigo-100 pb-4 mb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🏢</span>
                    <div>
                      <h2 className="text-2xl font-bold text-indigo-900">
                        {factoryDetail.company_name} - {factoryDetail.plant_name}
                      </h2>
                      <p className="text-sm text-indigo-600 mt-1">
                        工場ID: {factoryDetail.factory_id} |
                        {factoryDetail.lines?.length || 0}ライン |
                        {employees.length}名配属
                      </p>
                    </div>
                  </div>
                  {!isEditingFactory && (
                    <div className="flex gap-2">
                      <button
                        onClick={handleEditFactory}
                        className="px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      >
                        編集
                      </button>
                      <button
                        onClick={handleDeleteFactory}
                        className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        削除
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Factory Information Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Company Info Card */}
                <div className="border border-indigo-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📋</span>
                    <h3 className="font-semibold text-indigo-900">会社情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">会社名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.company_name || ''}
                          onChange={(e) => handleFieldChange('company_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.company_name}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">住所</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.company_address || ''}
                          onChange={(e) => handleFieldChange('company_address', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.company_address || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.company_phone || ''}
                          onChange={(e) => handleFieldChange('company_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.company_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Factory Info Card */}
                <div className="border border-indigo-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📍</span>
                    <h3 className="font-semibold text-indigo-900">工場情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">工場名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.plant_name || ''}
                          onChange={(e) => handleFieldChange('plant_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.plant_name}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">住所</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.plant_address || ''}
                          onChange={(e) => handleFieldChange('plant_address', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.plant_address || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.plant_phone || ''}
                          onChange={(e) => handleFieldChange('plant_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.plant_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Responsible Persons */}
                <div className="border border-indigo-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">👤</span>
                    <h3 className="font-semibold text-indigo-900">派遣先責任者</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">部署</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_responsible_department || ''}
                          onChange={(e) => handleFieldChange('client_responsible_department', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_responsible_department || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">氏名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_responsible_name || ''}
                          onChange={(e) => handleFieldChange('client_responsible_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_responsible_name || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_responsible_phone || ''}
                          onChange={(e) => handleFieldChange('client_responsible_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_responsible_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Complaint Contact */}
                <div className="border border-indigo-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📞</span>
                    <h3 className="font-semibold text-indigo-900">派遣先苦情担当</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">部署</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_complaint_department || ''}
                          onChange={(e) => handleFieldChange('client_complaint_department', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_complaint_department || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">氏名</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_complaint_name || ''}
                          onChange={(e) => handleFieldChange('client_complaint_name', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_complaint_name || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">電話</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.client_complaint_phone || ''}
                          onChange={(e) => handleFieldChange('client_complaint_phone', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.client_complaint_phone || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Information Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Contract & Schedule Card */}
                <div className="border border-indigo-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">📅</span>
                    <h3 className="font-semibold text-indigo-900">契約・スケジュール情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">契約開始日</label>
                      {isEditingFactory ? (
                        <input
                          type="date"
                          value={factoryFormData.contract_start_date || ''}
                          onChange={(e) => handleFieldChange('contract_start_date', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">
                          {factoryDetail.contract_start_date ?
                            new Date(factoryDetail.contract_start_date).toLocaleDateString('ja-JP') : '未設定'}
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">契約終了日</label>
                      {isEditingFactory ? (
                        <input
                          type="date"
                          value={factoryFormData.contract_end_date || ''}
                          onChange={(e) => handleFieldChange('contract_end_date', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">
                          {factoryDetail.contract_end_date ?
                            new Date(factoryDetail.contract_end_date).toLocaleDateString('ja-JP') : '未設定'}
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">就業時間</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.work_hours_description || ''}
                          onChange={(e) => handleFieldChange('work_hours_description', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.work_hours_description || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">昼勤開始</label>
                      {isEditingFactory ? (
                        <input
                          type="time"
                          value={factoryFormData.day_shift_start || ''}
                          onChange={(e) => handleFieldChange('day_shift_start', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.day_shift_start || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">昼勤終了</label>
                      {isEditingFactory ? (
                        <input
                          type="time"
                          value={factoryFormData.day_shift_end || ''}
                          onChange={(e) => handleFieldChange('day_shift_end', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.day_shift_end || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">夜勤開始</label>
                      {isEditingFactory ? (
                        <input
                          type="time"
                          value={factoryFormData.night_shift_start || ''}
                          onChange={(e) => handleFieldChange('night_shift_start', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.night_shift_start || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">夜勤終了</label>
                      {isEditingFactory ? (
                        <input
                          type="time"
                          value={factoryFormData.night_shift_end || ''}
                          onChange={(e) => handleFieldChange('night_shift_end', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.night_shift_end || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間外労働上限 (日)</label>
                      {isEditingFactory ? (
                        <input
                          type="number"
                          step="0.01"
                          value={factoryFormData.overtime_max_hours_day || ''}
                          onChange={(e) => handleFieldChange('overtime_max_hours_day', parseFloat(e.target.value))}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.overtime_max_hours_day ? `${factoryDetail.overtime_max_hours_day}時間` : '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間外労働上限 (月)</label>
                      {isEditingFactory ? (
                        <input
                          type="number"
                          step="0.01"
                          value={factoryFormData.overtime_max_hours_month || ''}
                          onChange={(e) => handleFieldChange('overtime_max_hours_month', parseFloat(e.target.value))}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.overtime_max_hours_month ? `${factoryDetail.overtime_max_hours_month}時間` : '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">休日労働上限 (月)</label>
                      {isEditingFactory ? (
                        <input
                          type="number"
                          step="1"
                          value={factoryFormData.holiday_work_max_days_month || ''}
                          onChange={(e) => handleFieldChange('holiday_work_max_days_month', parseInt(e.target.value))}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.holiday_work_max_days_month ? `${factoryDetail.holiday_work_max_days_month}日` : '-'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Payment & Agreement Card */}
                <div className="border border-indigo-200 rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">💰</span>
                    <h3 className="font-semibold text-indigo-900">支払・協定情報</h3>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">締め日</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.closing_date || ''}
                          onChange={(e) => handleFieldChange('closing_date', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.closing_date || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">支払日</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.payment_date || ''}
                          onChange={(e) => handleFieldChange('payment_date', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.payment_date || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">労働者締め日</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.worker_closing_date || ''}
                          onChange={(e) => handleFieldChange('worker_closing_date', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.worker_closing_date || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">労働者支払日</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.worker_payment_date || ''}
                          onChange={(e) => handleFieldChange('worker_payment_date', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.worker_payment_date || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">労働者カレンダー</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.worker_calendar || ''}
                          onChange={(e) => handleFieldChange('worker_calendar', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.worker_calendar || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">協定期間</label>
                      {isEditingFactory ? (
                        <input
                          type="date"
                          value={factoryFormData.agreement_period || ''}
                          onChange={(e) => handleFieldChange('agreement_period', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">
                          {factoryDetail.agreement_period ?
                            new Date(factoryDetail.agreement_period).toLocaleDateString('ja-JP') : '未設定'}
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">説明者</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.agreement_explainer || ''}
                          onChange={(e) => handleFieldChange('agreement_explainer', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.agreement_explainer || '-'}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間単位 (分)</label>
                      {isEditingFactory ? (
                        <input
                          type="number"
                          step="1"
                          value={factoryFormData.time_unit_minutes || 15}
                          onChange={(e) => handleFieldChange('time_unit_minutes', parseInt(e.target.value))}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.time_unit_minutes || '15'}分</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">銀行口座</label>
                      {isEditingFactory ? (
                        <input
                          type="text"
                          value={factoryFormData.bank_account || ''}
                          onChange={(e) => handleFieldChange('bank_account', e.target.value)}
                          className="w-full px-3 py-1 border border-gray-300 rounded-md"
                        />
                      ) : (
                        <p className="font-medium">{factoryDetail.bank_account || '-'}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Conflict Date (inline) */}
              <div className="flex flex-wrap gap-6 mb-4">
                <div>
                  <span className="text-sm text-gray-600">📅 抵触日:</span>
                  {isEditingFactory ? (
                    <input
                      type="date"
                      value={factoryFormData.conflict_date || ''}
                      onChange={(e) => handleFieldChange('conflict_date', e.target.value)}
                      className="ml-2 px-3 py-1 border border-gray-300 rounded-md"
                    />
                  ) : (
                    <span className="font-medium ml-2">
                      {factoryDetail.conflict_date ?
                        new Date(factoryDetail.conflict_date).toLocaleDateString('ja-JP') :
                        '未設定'
                      }
                    </span>
                  )}
                </div>
              </div>

              {/* Break Times Section - Multiple breaks per factory */}
              <div className="border-2 border-amber-300 rounded-lg p-4 mb-6 bg-amber-50/80">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">⏰</span>
                    <h3 className="font-bold text-amber-800 text-lg">休憩時間設定</h3>
                    <span className="text-xs bg-amber-200 text-amber-800 px-2 py-1 rounded-full font-semibold">
                      {factoryDetail.breaks?.filter((b: any) => b.is_active).length || 0}件
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      setEditingBreak(null)
                      setShowBreakModal(true)
                    }}
                    className="text-sm px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors font-medium shadow-sm"
                  >
                    ✏️ 編集・追加
                  </button>
                </div>

                {factoryDetail.breaks && factoryDetail.breaks.filter((b: any) => b.is_active).length > 0 ? (
                  <div className="grid gap-2">
                    {factoryDetail.breaks
                      .filter((b: any) => b.is_active)
                      .sort((a: any, b: any) => (a.display_order || 0) - (b.display_order || 0))
                      .map((breakItem: any) => (
                        <div
                          key={breakItem.id}
                          className="bg-white rounded-lg px-4 py-3 border border-amber-200 flex items-center justify-between shadow-sm"
                        >
                          <div className="flex items-center gap-4">
                            <span className="font-bold text-amber-700 min-w-[80px] text-base">
                              {breakItem.break_name}
                            </span>
                            {breakItem.break_start && breakItem.break_end && (
                              <span className="text-gray-700 font-mono">
                                {breakItem.break_start.slice(0, 5)} ~ {breakItem.break_end.slice(0, 5)}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                            {breakItem.break_minutes && (
                              <span className="text-base font-bold text-amber-600 bg-amber-100 px-2 py-1 rounded">
                                {breakItem.break_minutes}分
                              </span>
                            )}
                            {breakItem.description && (
                              <span className="text-sm text-gray-500 max-w-[200px] truncate">
                                ({breakItem.description})
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-amber-700 bg-white rounded-lg border-2 border-dashed border-amber-300">
                    <p className="text-base mb-2">⚠️ 休憩時間が設定されていません</p>
                    <p className="text-sm text-amber-600 mb-3">昼勤・夜勤・残業時の休憩を設定できます</p>
                    <button
                      onClick={() => {
                        setEditingBreak(null)
                        setShowBreakModal(true)
                      }}
                      className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors font-medium"
                    >
                      今すぐ設定する →
                    </button>
                  </div>
                )}
              </div>

              {/* Shift Schedule Section - Multiple shifts per factory (シフト管理) */}
              <div className="border-2 border-indigo-300 rounded-lg p-4 mb-6 bg-indigo-50/80">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">🕐</span>
                    <h3 className="font-bold text-indigo-800 text-lg">勤務シフト設定</h3>
                    <span className="text-xs bg-indigo-200 text-indigo-800 px-2 py-1 rounded-full font-semibold">
                      {factoryDetail.shifts?.filter((s: any) => s.is_active).length || 0}件
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      setEditingShift(null)
                      setShowShiftModal(true)
                    }}
                    className="text-sm px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-sm"
                  >
                    ✏️ 編集・追加
                  </button>
                </div>

                {factoryDetail.shifts && factoryDetail.shifts.filter((s: any) => s.is_active).length > 0 ? (
                  <div className="grid gap-2">
                    {factoryDetail.shifts
                      .filter((s: any) => s.is_active)
                      .sort((a: any, b: any) => (a.display_order || 0) - (b.display_order || 0))
                      .map((shift: any) => (
                        <div
                          key={shift.id}
                          className="bg-white rounded-lg px-4 py-3 border border-indigo-200 flex items-center justify-between shadow-sm"
                        >
                          <div className="flex items-center gap-4">
                            <span className="font-bold text-indigo-700 min-w-[100px] text-base">
                              {shift.shift_name}
                            </span>
                            {shift.shift_start && shift.shift_end && (
                              <span className="text-gray-700 font-mono">
                                {shift.shift_start.slice(0, 5)} ~ {shift.shift_end.slice(0, 5)}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                            {shift.shift_premium && (
                              <div className="flex items-center gap-1">
                                <span className="text-base font-bold text-indigo-600 bg-indigo-100 px-2 py-1 rounded">
                                  ¥{shift.shift_premium.toLocaleString()}
                                </span>
                                {shift.shift_premium_type && (
                                  <span className="text-xs text-indigo-600">/{shift.shift_premium_type}</span>
                                )}
                              </div>
                            )}
                            {shift.description && (
                              <span className="text-sm text-gray-500 max-w-[200px] truncate">
                                ({shift.description})
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-indigo-700 bg-white rounded-lg border-2 border-dashed border-indigo-300">
                    <p className="text-base mb-2">⚠️ 勤務シフトが設定されていません</p>
                    <p className="text-sm text-indigo-600 mb-3">昼勤・夜勤・第3シフト等を設定できます（手当付き）</p>
                    <button
                      onClick={() => {
                        setEditingShift(null)
                        setShowShiftModal(true)
                      }}
                      className="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors font-medium"
                    >
                      今すぐ設定する →
                    </button>
                  </div>
                )}
              </div>

              {/* Action Buttons for Factory Edit */}
              {isEditingFactory && (
                <div className="border-t pt-4 mb-6 flex justify-end gap-3">
                  <button
                    onClick={handleCancelEditFactory}
                    className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    disabled={updateFactoryMutation.isPending}
                  >
                    キャンセル
                  </button>
                  <button
                    onClick={handleSaveFactory}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm hover:shadow-md flex items-center gap-2"
                    disabled={updateFactoryMutation.isPending}
                  >
                    {updateFactoryMutation.isPending ? (
                      <>
                        <span className="animate-spin">⏳</span>
                        保存中...
                      </>
                    ) : (
                      <>
                        💾 保存する
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Production Lines Section */}
              <div className="border-t pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <h3 className="text-lg font-semibold">
                      生産ライン ({factoryDetail.lines?.length || 0})
                    </h3>
                    <span className="text-sm text-gray-500">
                      | 社員: {employees.length}名
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    {/* Employee Filter Checkbox */}
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={showAllEmployees}
                        onChange={(e) => setShowAllEmployees(e.target.checked)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-600">退社者も表示</span>
                    </label>
                    {!isEditingFactory && (
                      <button
                        onClick={() => router.push(`/factories/${selectedFactoryId}/lines/create`)}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm hover:shadow-md"
                      >
                        + ライン追加
                      </button>
                    )}
                  </div>
                </div>

                {/* LineCard Components */}
                {isLoadingEmployees ? (
                  <div className="space-y-3">
                    <SkeletonCard />
                    <SkeletonCard />
                  </div>
                ) : (
                  <div className="space-y-3">
                    {factoryDetail.lines && factoryDetail.lines.length > 0 ? (
                      factoryDetail.lines.map((line: FactoryLineResponse) => {
                        const lineEmployees = employeesByLine.get(line.id) || []
                        return (
                          <LineCard
                            key={line.id}
                            line={line}
                            employees={lineEmployees}
                            baseRate={line.hourly_rate}
                            onEdit={handleEditLine}
                            onDelete={handleDeleteLine}
                            isExpanded={expandedLines.has(line.id)}
                            onToggleExpand={() => toggleLineExpand(line.id)}
                          />
                        )
                      })
                    ) : (
                      <div className="bg-gray-50 rounded-lg p-8 text-center">
                        <span className="text-4xl mb-3 block">🏭</span>
                        <p className="text-gray-600">生産ラインが登録されていません</p>
                        <button
                          onClick={() => router.push(`/factories/${selectedFactoryId}/lines/create`)}
                          className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm hover:shadow-md"
                        >
                          最初のラインを追加
                        </button>
                      </div>
                    )}

                    {/* Employees without line assignment - grouped by line_name/department */}
                    {employeesByLine.has(null) && employeesByLine.get(null)!.length > 0 && (
                      <div className="mt-6 border-t pt-6">
                        <h4 className="text-lg font-medium mb-4 text-gray-700">
                          ライン未割当社員 ({employeesByLine.get(null)!.length}名) - Excelデータ別グループ
                        </h4>

                        <div className="space-y-4">
                          {unassignedByLineName.map(([groupName, groupEmployees]) => (
                            <div key={groupName} className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
                              {/* Group Header */}
                              <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="text-orange-500">📋</span>
                                  <span className="font-medium text-gray-800">{groupName}</span>
                                </div>
                                <span className="text-sm text-gray-600 bg-white px-2 py-0.5 rounded-full">
                                  {groupEmployees.length}名
                                </span>
                              </div>

                              {/* Employees Grid */}
                              <div className="p-3">
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                  {groupEmployees.map((emp) => (
                                    <div
                                      key={emp.id}
                                      className="bg-white rounded-md px-3 py-2 border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
                                    >
                                      <div className="text-sm font-medium text-gray-900">
                                        {emp.employee_number}
                                      </div>
                                      <div className="text-xs text-gray-700 font-medium">
                                        {emp.full_name_kanji || emp.display_name}
                                      </div>
                                      {emp.full_name_kana && (
                                        <div className="text-xs text-gray-500">
                                          {emp.full_name_kana}
                                        </div>
                                      )}
                                      {(emp as any).status === 'resigned' && (
                                        <span className="inline-block mt-1 text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded">
                                          退社
                                        </span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        <p className="mt-4 text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                          💡 これらの社員はExcelの配属先/ラインデータがありますが、システムのラインに紐付いていません。
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <EmptyState message={isLoadingDetail ? "読み込み中..." : "左側から工場を選択してください"} />
          )}
        </div>
      </div>

      {/* Modals */}
      {showShiftModal && selectedFactoryId && (
        <ShiftEditModal
          shift={editingShift}
          factoryId={selectedFactoryId}
          onSave={handleSaveShift}
          onClose={() => {
            setShowShiftModal(false)
            setEditingShift(null)
          }}
        />
      )}

      {showBreakModal && selectedFactoryId && (
        <BreakEditModal
          breakItem={editingBreak}
          factoryId={selectedFactoryId}
          onSave={handleSaveBreak}
          onClose={() => {
            setShowBreakModal(false)
            setEditingBreak(null)
          }}
        />
      )}
    </>
  )
}