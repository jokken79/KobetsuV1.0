'use client'

import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { importApi, ImportResponse } from '@/lib/api'

type ImportType = 'factories' | 'employees'
type ImportMode = 'create' | 'update' | 'sync'

export default function ImportPage() {
  const [importType, setImportType] = useState<ImportType>('factories')
  const [importMode, setImportMode] = useState<ImportMode>('sync')
  const [isDragging, setIsDragging] = useState(false)
  const [previewData, setPreviewData] = useState<ImportResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: async (file: File) => {
      if (importType === 'factories') {
        return importApi.previewFactories(file)
      } else {
        return importApi.previewEmployees(file)
      }
    },
    onSuccess: (data) => {
      setPreviewData(data)
    },
  })

  // Execute import mutation
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!previewData) return
      if (importType === 'factories') {
        return importApi.executeFactoryImport(previewData.preview_data, importMode)
      } else {
        return importApi.executeEmployeeImport(previewData.preview_data, importMode)
      }
    },
    onSuccess: (data) => {
      if (data) {
        setPreviewData(data)
      }
    },
  })

  // Sync mutation (one-click)
  const syncMutation = useMutation({
    mutationFn: async (file: File) => {
      return importApi.syncEmployees(file)
    },
    onSuccess: (data) => {
      setPreviewData(data)
    },
  })

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFile(files[0])
    }
  }, [importType])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFile(files[0])
    }
  }

  const handleFile = (file: File) => {
    setSelectedFile(file)
    setPreviewData(null)
    previewMutation.mutate(file)
  }

  const handleExecute = () => {
    executeMutation.mutate()
  }

  const handleQuickSync = () => {
    if (selectedFile) {
      syncMutation.mutate(selectedFile)
    }
  }

  const handleReset = () => {
    setPreviewData(null)
    setSelectedFile(null)
    previewMutation.reset()
    executeMutation.reset()
    syncMutation.reset()
  }

  const isLoading = previewMutation.isPending || executeMutation.isPending || syncMutation.isPending

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">データインポート</h1>

      {/* Import Type Selection */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={() => { setImportType('factories'); handleReset() }}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            importType === 'factories'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          工場マスタ
        </button>
        <button
          onClick={() => { setImportType('employees'); handleReset() }}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            importType === 'employees'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          従業員マスタ
        </button>
      </div>

      {/* Template Download */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600 mb-2">テンプレートをダウンロード:</p>
        <div className="flex gap-2">
          {importType === 'factories' ? (
            <>
              <a
                href={importApi.downloadFactoryTemplate('excel')}
                className="text-blue-600 hover:underline text-sm"
                download
              >
                Excel テンプレート
              </a>
              <span className="text-gray-400">|</span>
              <a
                href={importApi.downloadFactoryTemplate('json')}
                className="text-blue-600 hover:underline text-sm"
                download
              >
                JSON テンプレート
              </a>
            </>
          ) : (
            <a
              href={importApi.downloadEmployeeTemplate()}
              className="text-blue-600 hover:underline text-sm"
              download
            >
              Excel テンプレート
            </a>
          )}
        </div>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <div className="mb-4">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <p className="text-lg text-gray-600 mb-2">
          ファイルをドラッグ＆ドロップ
        </p>
        <p className="text-sm text-gray-500 mb-4">
          {importType === 'factories'
            ? 'JSON または Excel (.xlsx, .xlsm)'
            : 'Excel (.xlsx, .xlsm)'}
        </p>
        <label className="inline-block">
          <span className="px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700">
            ファイルを選択
          </span>
          <input
            type="file"
            className="hidden"
            accept={importType === 'factories' ? '.json,.xlsx,.xls,.xlsm' : '.xlsx,.xls,.xlsm'}
            onChange={handleFileSelect}
          />
        </label>

        {selectedFile && (
          <p className="mt-4 text-sm text-gray-600">
            選択中: {selectedFile.name}
          </p>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg flex items-center justify-center">
          <svg className="animate-spin h-5 w-5 mr-3 text-blue-600" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-blue-600">処理中...</span>
        </div>
      )}

      {/* Preview Results */}
      {previewData && !isLoading && (
        <div className="mt-6">
          {/* Summary */}
          <div className={`p-4 rounded-lg mb-4 ${
            previewData.success ? 'bg-green-50' : 'bg-yellow-50'
          }`}>
            <p className={`font-medium ${previewData.success ? 'text-green-800' : 'text-yellow-800'}`}>
              {previewData.message}
            </p>
            <div className="mt-2 text-sm text-gray-600 grid grid-cols-4 gap-4">
              <div>
                <span className="font-medium">合計:</span> {previewData.total_rows}件
              </div>
              {previewData.imported_count > 0 && (
                <div>
                  <span className="font-medium text-green-600">新規:</span> {previewData.imported_count}件
                </div>
              )}
              {previewData.updated_count > 0 && (
                <div>
                  <span className="font-medium text-blue-600">更新:</span> {previewData.updated_count}件
                </div>
              )}
              {previewData.skipped_count > 0 && (
                <div>
                  <span className="font-medium text-gray-600">スキップ:</span> {previewData.skipped_count}件
                </div>
              )}
            </div>
          </div>

          {/* Errors */}
          {previewData.errors.length > 0 && (
            <div className="mb-4 p-4 bg-red-50 rounded-lg">
              <p className="font-medium text-red-800 mb-2">
                エラー ({previewData.errors.length}件)
              </p>
              <ul className="text-sm text-red-700 max-h-40 overflow-auto">
                {previewData.errors.map((error, idx) => (
                  <li key={idx} className="mb-1">
                    行 {error.row}: {error.message}
                    {error.value && <span className="text-red-500"> (値: {error.value})</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Preview Table */}
          {previewData.preview_data.length > 0 && (
            <div className="bg-white rounded-lg border overflow-hidden">
              <div className="p-4 border-b bg-gray-50">
                <h3 className="font-medium">プレビュー (最大100件)</h3>
              </div>
              <div className="overflow-auto max-h-96">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">行</th>
                      <th className="px-4 py-2 text-left">状態</th>
                      {importType === 'factories' ? (
                        <>
                          <th className="px-4 py-2 text-left">派遣先名</th>
                          <th className="px-4 py-2 text-left">工場名</th>
                          <th className="px-4 py-2 text-left">抵触日</th>
                        </>
                      ) : (
                        <>
                          <th className="px-4 py-2 text-left">社員№</th>
                          <th className="px-4 py-2 text-left">氏名</th>
                          <th className="px-4 py-2 text-left">カナ</th>
                          <th className="px-4 py-2 text-left">派遣先</th>
                          <th className="px-4 py-2 text-left">時給</th>
                        </>
                      )}
                      <th className="px-4 py-2 text-left">エラー</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.preview_data.map((item, idx) => (
                      <tr key={idx} className={`border-b ${!item.is_valid ? 'bg-red-50' : ''}`}>
                        <td className="px-4 py-2">{item.row}</td>
                        <td className="px-4 py-2">
                          {item.is_valid ? (
                            <span className="text-green-600">OK</span>
                          ) : (
                            <span className="text-red-600">NG</span>
                          )}
                        </td>
                        {importType === 'factories' ? (
                          <>
                            <td className="px-4 py-2">{String(item.company_name || '')}</td>
                            <td className="px-4 py-2">{String(item.plant_name || '')}</td>
                            <td className="px-4 py-2">{String(item.conflict_date || '')}</td>
                          </>
                        ) : (
                          <>
                            <td className="px-4 py-2">{String(item.employee_number || '')}</td>
                            <td className="px-4 py-2">{String(item.full_name_kanji || '')}</td>
                            <td className="px-4 py-2">{String(item.full_name_kana || '')}</td>
                            <td className="px-4 py-2">{String(item.company_name || '')}</td>
                            <td className="px-4 py-2">{item.hourly_rate ? `¥${item.hourly_rate}` : ''}</td>
                          </>
                        )}
                        <td className="px-4 py-2 text-red-600 text-xs">
                          {item.errors?.join(', ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {previewData.preview_data.length > 0 && !executeMutation.isSuccess && (
            <div className="mt-6 flex gap-4">
              {/* Import Mode Selection */}
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">モード:</label>
                <select
                  value={importMode}
                  onChange={(e) => setImportMode(e.target.value as ImportMode)}
                  className="border rounded px-3 py-2 text-sm"
                >
                  <option value="create">新規のみ作成</option>
                  <option value="update">既存のみ更新</option>
                  <option value="sync">同期 (新規+更新)</option>
                </select>
              </div>

              <button
                onClick={handleExecute}
                disabled={isLoading || previewData.errors.length > 0}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                インポート実行
              </button>

              {importType === 'employees' && (
                <button
                  onClick={handleQuickSync}
                  disabled={isLoading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  クイック同期
                </button>
              )}

              <button
                onClick={handleReset}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                リセット
              </button>
            </div>
          )}

          {/* Success Message */}
          {executeMutation.isSuccess && (
            <div className="mt-6 p-4 bg-green-100 rounded-lg">
              <p className="text-green-800 font-medium">インポートが完了しました</p>
              <button
                onClick={handleReset}
                className="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                新しいインポートを開始
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
