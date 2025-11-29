'use client'

/**
 * Sync Page - Data Synchronization from Master Files
 *
 * Synchronizes employees and factories from master files
 * configured in the backend environment.
 */

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { syncApi, SyncResult, SyncStatus } from '@/lib/api'
import { AxiosError } from 'axios'

interface SyncResultState {
  type: string
  success: boolean
  data?: SyncResult
  error?: string
}

export default function SyncPage() {
  const [lastSyncResult, setLastSyncResult] = useState<SyncResultState | null>(null)
  const queryClient = useQueryClient()

  // Query to get current status
  const { data: status, isLoading: statusLoading } = useQuery<SyncStatus>({
    queryKey: ['syncStatus'],
    queryFn: syncApi.getStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Mutation to sync employees
  const syncEmployeesMutation = useMutation({
    mutationFn: syncApi.syncEmployees,
    onSuccess: (data) => {
      setLastSyncResult({
        type: 'employees',
        success: true,
        data
      })
      queryClient.invalidateQueries({ queryKey: ['syncStatus'] })
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      setLastSyncResult({
        type: 'employees',
        success: false,
        error: error.response?.data?.detail || error.message
      })
    }
  })

  // Mutation to sync factories
  const syncFactoriesMutation = useMutation({
    mutationFn: syncApi.syncFactories,
    onSuccess: (data) => {
      setLastSyncResult({
        type: 'factories',
        success: true,
        data
      })
      queryClient.invalidateQueries({ queryKey: ['syncStatus'] })
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      setLastSyncResult({
        type: 'factories',
        success: false,
        error: error.response?.data?.detail || error.message
      })
    }
  })

  // Mutation to sync everything
  const syncAllMutation = useMutation({
    mutationFn: syncApi.syncAll,
    onSuccess: (data) => {
      setLastSyncResult({
        type: 'all',
        success: true,
        data
      })
      queryClient.invalidateQueries({ queryKey: ['syncStatus'] })
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      setLastSyncResult({
        type: 'all',
        success: false,
        error: error.response?.data?.detail || error.message
      })
    }
  })

  const isAnySyncing =
    syncEmployeesMutation.isPending ||
    syncFactoriesMutation.isPending ||
    syncAllMutation.isPending

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Data Sync</h1>
        <p className="text-gray-600 mt-2">
          Synchronize employee and factory data from network master files
        </p>
      </div>

      {/* Current Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Current Status</h2>
        {statusLoading ? (
          <p>Loading...</p>
        ) : status ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">Employees</h3>
              <div className="space-y-1 text-sm">
                <p>Total: {status.employees?.total || 0}</p>
                <p>Active: {status.employees?.active || 0}</p>
                <p>Resigned: {status.employees?.resigned || 0}</p>
              </div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">Factories</h3>
              <div className="space-y-1 text-sm">
                <p>Companies/Plants: {status.factories?.total || 0}</p>
                <p>Lines: {status.factories?.lines || 0}</p>
              </div>
            </div>
          </div>
        ) : (
          <p>Unable to load data</p>
        )}
      </div>

      {/* Sync Buttons */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Sync Options</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Sync Employees */}
          <button
            onClick={() => syncEmployeesMutation.mutate()}
            disabled={isAnySyncing}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {syncEmployeesMutation.isPending ? (
              <span>Syncing...</span>
            ) : (
              <span>Sync Employees</span>
            )}
          </button>

          {/* Sync Factories */}
          <button
            onClick={() => syncFactoriesMutation.mutate()}
            disabled={isAnySyncing}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {syncFactoriesMutation.isPending ? (
              <span>Syncing...</span>
            ) : (
              <span>Sync Factories</span>
            )}
          </button>

          {/* Sync All */}
          <button
            onClick={() => syncAllMutation.mutate()}
            disabled={isAnySyncing}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {syncAllMutation.isPending ? (
              <span>Syncing...</span>
            ) : (
              <span>Sync All</span>
            )}
          </button>
        </div>

        <div className="mt-4 text-sm text-gray-600">
          <p>Data is synchronized from network paths configured in the backend environment.</p>
        </div>
      </div>

      {/* Last Sync Result */}
      {lastSyncResult && (
        <div className={`rounded-lg shadow-sm border p-6 ${
          lastSyncResult.success
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <h2 className="text-xl font-semibold mb-4">
            {lastSyncResult.success ? 'Sync Successful' : 'Sync Error'}
          </h2>

          {lastSyncResult.success && lastSyncResult.data ? (
            <div className="space-y-3">
              {/* Employees */}
              {lastSyncResult.data.employees && (
                <div className="bg-white rounded p-4">
                  <h3 className="font-semibold mb-2">Employees</h3>
                  <div className="text-sm space-y-1">
                    <p>Processed: {lastSyncResult.data.employees.total || 0}</p>
                    <p>Created: {lastSyncResult.data.employees.created || 0}</p>
                    <p>Updated: {lastSyncResult.data.employees.updated || 0}</p>
                    {lastSyncResult.data.employees.errors?.length > 0 && (
                      <p className="text-red-600">
                        Errors: {lastSyncResult.data.employees.errors.length}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Factories */}
              {lastSyncResult.data.factories && (
                <div className="bg-white rounded p-4">
                  <h3 className="font-semibold mb-2">Factories</h3>
                  <div className="text-sm space-y-1">
                    <p>Processed: {lastSyncResult.data.factories.total || 0}</p>
                    <p>Created: {lastSyncResult.data.factories.created || 0}</p>
                    <p>Updated: {lastSyncResult.data.factories.updated || 0}</p>
                    {lastSyncResult.data.factories.errors?.length > 0 && (
                      <p className="text-red-600">
                        Errors: {lastSyncResult.data.factories.errors.length}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {lastSyncResult.data.elapsed_seconds && (
                <p className="text-sm text-gray-600">
                  Elapsed time: {lastSyncResult.data.elapsed_seconds.toFixed(2)}s
                </p>
              )}
            </div>
          ) : (
            <div className="text-red-700">
              <p className="font-medium">An error occurred:</p>
              <p className="mt-2 text-sm">{lastSyncResult.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
