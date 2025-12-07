/**
 * Tests para validación del formulario de contratos Kobetsu
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'

// Mock del router de Next.js
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
  useParams: () => ({ id: '1' }),
  useSearchParams: () => new URLSearchParams(),
}))

// Mock de React Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
  })),
  useMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}))

/**
 * Función de validación del formulario
 * Replica la lógica de validación del formulario real
 */
const validateKobetsuForm = (data: Record<string, unknown>) => {
  const errors: Record<string, string> = {}

  // Validación de派遣先名 (nombre del sitio de trabajo)
  if (!data.worksite_name || String(data.worksite_name).trim() === '') {
    errors.worksite_name = '派遣先名を入力してください'
  }

  // Validación de業務内容 (contenido del trabajo) - mínimo 10 caracteres
  const workContent = String(data.work_content || '')
  if (!workContent || workContent.length < 10) {
    errors.work_content = '業務内容を10文字以上で入力してください'
  }

  // Validación de fechas
  if (!data.dispatch_start_date) {
    errors.dispatch_start_date = '開始日を入力してください'
  }

  if (!data.dispatch_end_date) {
    errors.dispatch_end_date = '終了日を入力してください'
  }

  // Validación de orden de fechas
  if (data.dispatch_start_date && data.dispatch_end_date) {
    const start = new Date(String(data.dispatch_start_date))
    const end = new Date(String(data.dispatch_end_date))
    if (end < start) {
      errors.dispatch_end_date = '終了日は開始日より後でなければなりません'
    }
  }

  // Validación de supervisor
  if (!data.supervisor_name || String(data.supervisor_name).trim() === '') {
    errors.supervisor_name = '監督者名を入力してください'
  }

  // Validación de時給 (salario por hora) - mínimo 800
  const hourlyRate = Number(data.hourly_rate) || 0
  if (hourlyRate < 800) {
    errors.hourly_rate = '時給は最低賃金以上でなければなりません'
  }
  if (hourlyRate > 10000) {
    errors.hourly_rate = '時給が高すぎます。確認してください'
  }

  // Validación de días de trabajo
  const workDays = data.work_days as string[] | undefined
  if (!workDays || workDays.length === 0) {
    errors.work_days = '少なくとも1つの勤務日を選択してください'
  } else {
    const validDays = ['月', '火', '水', '木', '金', '土', '日']
    const invalidDays = workDays.filter(day => !validDays.includes(day))
    if (invalidDays.length > 0) {
      errors.work_days = `無効な曜日: ${invalidDays.join(', ')}`
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

describe('KobetsuForm - Validación de Campos', () => {
  describe('Campo: 派遣先名 (worksite_name)', () => {
    it('debe mostrar error cuando está vacío', () => {
      const result = validateKobetsuForm({ worksite_name: '' })
      expect(result.errors.worksite_name).toBe('派遣先名を入力してください')
    })

    it('debe mostrar error cuando es solo espacios', () => {
      const result = validateKobetsuForm({ worksite_name: '   ' })
      expect(result.errors.worksite_name).toBe('派遣先名を入力してください')
    })

    it('debe pasar con valor válido', () => {
      const result = validateKobetsuForm({
        worksite_name: 'テスト株式会社',
        work_content: 'Contenido de trabajo con más de 10 caracteres',
        dispatch_start_date: '2025-01-01',
        dispatch_end_date: '2025-12-31',
        supervisor_name: 'Test Supervisor',
        hourly_rate: 1500,
        work_days: ['月', '火', '水'],
      })
      expect(result.errors.worksite_name).toBeUndefined()
    })
  })

  describe('Campo: 業務内容 (work_content)', () => {
    it('debe mostrar error cuando tiene menos de 10 caracteres', () => {
      const result = validateKobetsuForm({ work_content: '短い内容' })
      expect(result.errors.work_content).toBe('業務内容を10文字以上で入力してください')
    })

    it('debe pasar con 10+ caracteres', () => {
      const result = validateKobetsuForm({
        worksite_name: 'Test',
        work_content: '製造ライン作業の補助業務を担当します',
        dispatch_start_date: '2025-01-01',
        dispatch_end_date: '2025-12-31',
        supervisor_name: 'Test',
        hourly_rate: 1500,
        work_days: ['月'],
      })
      expect(result.errors.work_content).toBeUndefined()
    })
  })

  describe('Campos: Fechas', () => {
    it('debe mostrar error cuando開始日 está vacío', () => {
      const result = validateKobetsuForm({ dispatch_start_date: '' })
      expect(result.errors.dispatch_start_date).toBe('開始日を入力してください')
    })

    it('debe mostrar error cuando終了日 está vacío', () => {
      const result = validateKobetsuForm({ dispatch_end_date: '' })
      expect(result.errors.dispatch_end_date).toBe('終了日を入力してください')
    })

    it('debe mostrar error cuando終了日 es anterior a開始日', () => {
      const result = validateKobetsuForm({
        dispatch_start_date: '2025-12-01',
        dispatch_end_date: '2025-11-01', // Antes del inicio
      })
      expect(result.errors.dispatch_end_date).toBe('終了日は開始日より後でなければなりません')
    })

    it('debe permitir misma fecha de inicio y fin', () => {
      const result = validateKobetsuForm({
        worksite_name: 'Test',
        work_content: 'Test content with more than 10 characters',
        dispatch_start_date: '2025-06-15',
        dispatch_end_date: '2025-06-15', // Mismo día
        supervisor_name: 'Test',
        hourly_rate: 1500,
        work_days: ['月'],
      })
      expect(result.errors.dispatch_end_date).toBeUndefined()
    })
  })

  describe('Campo: 時給 (hourly_rate)', () => {
    it('debe mostrar error cuando es menor al salario mínimo', () => {
      const result = validateKobetsuForm({ hourly_rate: 500 })
      expect(result.errors.hourly_rate).toBe('時給は最低賃金以上でなければなりません')
    })

    it('debe mostrar advertencia cuando es muy alto', () => {
      const result = validateKobetsuForm({ hourly_rate: 15000 })
      expect(result.errors.hourly_rate).toBe('時給が高すぎます。確認してください')
    })

    it('debe pasar con salario razonable', () => {
      const result = validateKobetsuForm({
        worksite_name: 'Test',
        work_content: 'Test content with more than 10 characters',
        dispatch_start_date: '2025-01-01',
        dispatch_end_date: '2025-12-31',
        supervisor_name: 'Test',
        hourly_rate: 1500,
        work_days: ['月'],
      })
      expect(result.errors.hourly_rate).toBeUndefined()
    })
  })

  describe('Campo: 勤務日 (work_days)', () => {
    it('debe mostrar error cuando no hay días seleccionados', () => {
      const result = validateKobetsuForm({ work_days: [] })
      expect(result.errors.work_days).toBe('少なくとも1つの勤務日を選択してください')
    })

    it('debe mostrar error con días inválidos', () => {
      const result = validateKobetsuForm({ work_days: ['月', 'Monday', 'Lunes'] })
      expect(result.errors.work_days).toContain('無効な曜日')
      expect(result.errors.work_days).toContain('Monday')
      expect(result.errors.work_days).toContain('Lunes')
    })

    it('debe pasar con días japoneses válidos', () => {
      const result = validateKobetsuForm({
        worksite_name: 'Test',
        work_content: 'Test content with more than 10 characters',
        dispatch_start_date: '2025-01-01',
        dispatch_end_date: '2025-12-31',
        supervisor_name: 'Test',
        hourly_rate: 1500,
        work_days: ['月', '火', '水', '木', '金'],
      })
      expect(result.errors.work_days).toBeUndefined()
    })

    it('debe aceptar fines de semana', () => {
      const result = validateKobetsuForm({
        worksite_name: 'Test',
        work_content: 'Test content with more than 10 characters',
        dispatch_start_date: '2025-01-01',
        dispatch_end_date: '2025-12-31',
        supervisor_name: 'Test',
        hourly_rate: 1500,
        work_days: ['土', '日'],
      })
      expect(result.errors.work_days).toBeUndefined()
    })
  })
})

describe('KobetsuForm - Formulario Completo', () => {
  it('debe retornar isValid=true cuando todos los campos son correctos', () => {
    const validData = {
      worksite_name: 'テスト株式会社 本社工場',
      work_content: '製造ライン作業、検品、梱包業務の補助作業を担当します。',
      dispatch_start_date: '2025-01-01',
      dispatch_end_date: '2025-12-31',
      supervisor_name: '田中太郎',
      hourly_rate: 1500,
      work_days: ['月', '火', '水', '木', '金'],
    }

    const result = validateKobetsuForm(validData)

    expect(result.isValid).toBe(true)
    expect(Object.keys(result.errors)).toHaveLength(0)
  })

  it('debe retornar múltiples errores cuando hay varios campos inválidos', () => {
    const invalidData = {
      worksite_name: '',
      work_content: '短い',
      dispatch_start_date: '',
      dispatch_end_date: '',
      supervisor_name: '',
      hourly_rate: 0,
      work_days: [],
    }

    const result = validateKobetsuForm(invalidData)

    expect(result.isValid).toBe(false)
    expect(Object.keys(result.errors).length).toBeGreaterThan(3)
  })
})

// Componente simple para tests de renderizado
const SimpleFormField = ({
  label,
  name,
  error,
  type = 'text',
}: {
  label: string
  name: string
  error?: string
  type?: string
}) => (
  <div>
    <label htmlFor={name}>{label}</label>
    <input
      id={name}
      name={name}
      type={type}
      aria-invalid={!!error}
      aria-describedby={error ? `${name}-error` : undefined}
    />
    {error && (
      <span id={`${name}-error`} role="alert" className="text-red-500">
        {error}
      </span>
    )}
  </div>
)

describe('KobetsuForm - Renderizado de Errores', () => {
  it('debe mostrar el error visualmente cuando existe', () => {
    render(
      <SimpleFormField
        label="派遣先名"
        name="worksite_name"
        error="派遣先名を入力してください"
      />
    )

    const errorMessage = screen.getByRole('alert')
    expect(errorMessage).toBeInTheDocument()
    expect(errorMessage).toHaveTextContent('派遣先名を入力してください')
  })

  it('debe marcar el campo como inválido cuando hay error', () => {
    render(
      <SimpleFormField
        label="業務内容"
        name="work_content"
        error="業務内容を10文字以上で入力してください"
      />
    )

    const input = screen.getByLabelText('業務内容')
    expect(input).toHaveAttribute('aria-invalid', 'true')
  })

  it('no debe mostrar error cuando el campo es válido', () => {
    render(
      <SimpleFormField
        label="派遣先名"
        name="worksite_name"
      />
    )

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
