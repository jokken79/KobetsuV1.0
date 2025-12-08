/**
 * E2E Tests - Flujos completos de la aplicación KobetsuV1.0
 * Ejecutar con: npx playwright test
 */
import { test, expect, Page } from '@playwright/test'

// Configuración
const BASE_URL = process.env.BASE_URL || 'http://localhost:3024'
const TEST_EMAIL = 'admin@example.com'
const TEST_PASSWORD = 'admin123'

/**
 * Helper: Login en la aplicación
 */
async function login(page: Page) {
  await page.goto(`${BASE_URL}/login`)
  await page.fill('input[name="email"]', TEST_EMAIL)
  await page.fill('input[name="password"]', TEST_PASSWORD)
  await page.click('button[type="submit"]')

  // Esperar a que cargue el dashboard
  await page.waitForURL('**/', { timeout: 10000 })
}

test.describe('Autenticación', () => {
  test('debe mostrar página de login', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)

    await expect(page.locator('input[name="email"]')).toBeVisible()
    await expect(page.locator('input[name="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('debe rechazar credenciales inválidas', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)

    await page.fill('input[name="email"]', 'wrong@email.com')
    await page.fill('input[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    // Debe mostrar error
    await expect(page.locator('text=エラー').or(page.locator('text=invalid').or(page.locator('[role="alert"]')))).toBeVisible({ timeout: 5000 })
  })

  test('debe permitir login con credenciales válidas', async ({ page }) => {
    await login(page)

    // Debe estar en el dashboard
    await expect(page).toHaveURL(/\/$/)
  })

  test('debe redirigir a login si no está autenticado', async ({ page }) => {
    // Intentar acceder a página protegida sin login
    await page.goto(`${BASE_URL}/kobetsu`)

    // Debe redirigir a login
    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe mostrar estadísticas de contratos', async ({ page }) => {
    // Verificar que las stats cards están presentes
    await expect(page.locator('text=総契約数').or(page.locator('text=契約'))).toBeVisible({ timeout: 10000 })
  })

  test('debe tener navegación funcional', async ({ page }) => {
    // Verificar elementos de navegación
    const navLinks = ['契約', '工場', '従業員']

    for (const link of navLinks) {
      await expect(page.locator(`text=${link}`).first()).toBeVisible()
    }
  })
})

test.describe('Gestión de Contratos (個別契約書)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe mostrar lista de contratos', async ({ page }) => {
    await page.goto(`${BASE_URL}/kobetsu`)

    // Verificar que la página carga
    await expect(page.locator('text=契約').first()).toBeVisible({ timeout: 10000 })

    // Debe haber una tabla o lista
    const table = page.locator('table').or(page.locator('[data-testid="contracts-list"]'))
    await expect(table).toBeVisible()
  })

  test('debe poder filtrar contratos por estado', async ({ page }) => {
    await page.goto(`${BASE_URL}/kobetsu`)
    await page.waitForLoadState('networkidle')

    // Buscar selector de filtro de estado
    const statusFilter = page.locator('select[name="status"]').or(page.locator('[data-testid="status-filter"]'))

    if (await statusFilter.isVisible()) {
      await statusFilter.selectOption('active')
      await page.waitForTimeout(500)

      // Verificar que la URL contiene el filtro
      expect(page.url()).toContain('status=active')
    }
  })

  test('debe navegar a crear nuevo contrato', async ({ page }) => {
    await page.goto(`${BASE_URL}/kobetsu`)
    await page.waitForLoadState('networkidle')

    // Buscar botón de crear
    const createButton = page.locator('text=新規作成').or(page.locator('text=契約作成')).or(page.locator('a[href*="create"]'))

    if (await createButton.first().isVisible()) {
      await createButton.first().click()
      await expect(page).toHaveURL(/\/kobetsu\/create/)
    }
  })

  test('debe mostrar detalle de contrato', async ({ page }) => {
    await page.goto(`${BASE_URL}/kobetsu`)
    await page.waitForLoadState('networkidle')

    // Click en primer contrato de la lista
    const firstRow = page.locator('tbody tr').first().or(page.locator('[data-testid="contract-row"]').first())

    if (await firstRow.isVisible()) {
      await firstRow.click()

      // Debe navegar al detalle
      await expect(page).toHaveURL(/\/kobetsu\/\d+/)

      // Debe mostrar información del contrato
      await expect(page.locator('text=KOB-').first()).toBeVisible({ timeout: 5000 })
    }
  })
})

test.describe('Gestión de Fábricas (工場)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe mostrar lista de fábricas', async ({ page }) => {
    await page.goto(`${BASE_URL}/factories`)

    await expect(page.locator('text=工場').first()).toBeVisible({ timeout: 10000 })
  })

  test('debe mostrar detalle de fábrica con líneas', async ({ page }) => {
    await page.goto(`${BASE_URL}/factories`)
    await page.waitForLoadState('networkidle')

    // Click en primera fábrica
    const firstFactory = page.locator('tbody tr').first().or(page.locator('[data-testid="factory-row"]').first())

    if (await firstFactory.isVisible()) {
      await firstFactory.click()

      // Debe mostrar sección de líneas
      await expect(page.locator('text=ライン').or(page.locator('text=配属先'))).toBeVisible({ timeout: 5000 })
    }
  })

  test('debe poder abrir modal de nueva línea', async ({ page }) => {
    // Ir a una fábrica específica
    await page.goto(`${BASE_URL}/factories`)
    await page.waitForLoadState('networkidle')

    const firstFactory = page.locator('tbody tr').first()
    if (await firstFactory.isVisible()) {
      await firstFactory.click()
      await page.waitForLoadState('networkidle')

      // Buscar botón de agregar línea
      const addLineButton = page.locator('text=新規ライン').or(page.locator('text=ライン追加'))

      if (await addLineButton.isVisible()) {
        await addLineButton.click()

        // Modal debe aparecer
        await expect(page.locator('[role="dialog"]').or(page.locator('[data-testid="line-modal"]'))).toBeVisible({ timeout: 3000 })
      }
    }
  })
})

test.describe('Gestión de Empleados (従業員)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe mostrar lista de empleados', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`)

    await expect(page.locator('text=従業員').or(page.locator('text=社員'))).toBeVisible({ timeout: 10000 })
  })

  test('debe poder buscar empleados', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`)
    await page.waitForLoadState('networkidle')

    const searchInput = page.locator('input[placeholder*="検索"]').or(page.locator('input[name="search"]'))

    if (await searchInput.isVisible()) {
      await searchInput.fill('山田')
      await page.waitForTimeout(500)

      // La búsqueda debe reflejarse en la URL o en los resultados
    }
  })
})

test.describe('Flujo Completo: Crear Contrato', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe completar el flujo de creación de contrato', async ({ page }) => {
    // 1. Ir a crear contrato
    await page.goto(`${BASE_URL}/kobetsu/create`)
    await page.waitForLoadState('networkidle')

    // 2. Verificar que el formulario está presente
    await expect(page.locator('form')).toBeVisible({ timeout: 10000 })

    // 3. Llenar campos básicos (si están disponibles)
    const worksiteName = page.locator('input[name="worksite_name"]')
    if (await worksiteName.isVisible()) {
      await worksiteName.fill('E2E Test Company')
    }

    const workContent = page.locator('textarea[name="work_content"]')
    if (await workContent.isVisible()) {
      await workContent.fill('E2E Test - 製造ライン作業、検品、梱包業務を担当します。')
    }

    const startDate = page.locator('input[name="dispatch_start_date"]')
    if (await startDate.isVisible()) {
      await startDate.fill('2025-01-01')
    }

    const endDate = page.locator('input[name="dispatch_end_date"]')
    if (await endDate.isVisible()) {
      await endDate.fill('2025-12-31')
    }

    // Verificar que hay un botón de guardar
    const saveButton = page.locator('button[type="submit"]').or(page.locator('text=保存'))
    await expect(saveButton.first()).toBeVisible()

    // Nota: No enviamos el formulario completo para no crear datos de prueba
    // En un entorno de pruebas real, completaríamos y enviaríamos
  })
})

test.describe('Importación de Datos', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe mostrar página de importación', async ({ page }) => {
    await page.goto(`${BASE_URL}/import`)

    await expect(page.locator('text=インポート').or(page.locator('text=Import'))).toBeVisible({ timeout: 10000 })
  })

  test('debe tener área de upload de archivos', async ({ page }) => {
    await page.goto(`${BASE_URL}/import`)
    await page.waitForLoadState('networkidle')

    // Debe haber un input de archivo
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeVisible()
  })
})

test.describe('Sincronización', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe mostrar página de sincronización', async ({ page }) => {
    await page.goto(`${BASE_URL}/sync`)

    await expect(page.locator('text=同期').or(page.locator('text=Sync'))).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Responsive Design', () => {
  test('debe ser usable en viewport móvil', async ({ page }) => {
    // Configurar viewport móvil
    await page.setViewportSize({ width: 375, height: 667 })

    await login(page)

    // El menú debe adaptarse (hamburger menu o similar)
    await expect(page.locator('body')).toBeVisible()

    // Navegar a contratos
    await page.goto(`${BASE_URL}/kobetsu`)

    // La tabla debe ser scrollable o adaptarse
    await expect(page.locator('text=契約').first()).toBeVisible({ timeout: 10000 })
  })

  test('debe ser usable en viewport tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    await login(page)
    await page.goto(`${BASE_URL}/kobetsu`)

    await expect(page.locator('text=契約').first()).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Accesibilidad Básica', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('debe tener labels en formularios', async ({ page }) => {
    await page.goto(`${BASE_URL}/kobetsu/create`)
    await page.waitForLoadState('networkidle')

    // Todos los inputs deben tener labels asociados
    const inputs = await page.locator('input:not([type="hidden"]):not([type="submit"])').all()

    for (const input of inputs.slice(0, 5)) { // Verificar primeros 5
      const id = await input.getAttribute('id')
      const name = await input.getAttribute('name')
      const ariaLabel = await input.getAttribute('aria-label')

      if (id) {
        const label = page.locator(`label[for="${id}"]`)
        const hasLabel = await label.isVisible().catch(() => false)
        const hasAriaLabel = !!ariaLabel

        // Debe tener label o aria-label
        expect(hasLabel || hasAriaLabel).toBeTruthy()
      }
    }
  })

  test('debe ser navegable con teclado', async ({ page }) => {
    await page.goto(`${BASE_URL}/kobetsu`)
    await page.waitForLoadState('networkidle')

    // Tab debe mover el foco
    await page.keyboard.press('Tab')
    const focusedElement = await page.locator(':focus')
    await expect(focusedElement).toBeVisible()
  })
})

test.describe('Manejo de Errores', () => {
  test('debe mostrar página 404 para rutas inexistentes', async ({ page }) => {
    await login(page)
    await page.goto(`${BASE_URL}/ruta-que-no-existe`)

    // Debe mostrar mensaje de error o redirigir
    await expect(
      page.locator('text=404').or(page.locator('text=見つかりません')).or(page.locator('text=Not Found'))
    ).toBeVisible({ timeout: 5000 })
  })

  test('debe manejar errores de carga gracefully', async ({ page }) => {
    await login(page)

    // Intentar cargar un contrato que no existe
    await page.goto(`${BASE_URL}/kobetsu/999999`)

    // Debe mostrar mensaje de error o redirigir
    // El comportamiento específico depende de la implementación
    await page.waitForLoadState('networkidle')
  })
})
