# 🔗 Kobetsu Keiyakusho - Integrado con Super Base Madre

Este es un **fork mejorado** de UNS-Kobetsu-Keiyakusho que incluye integración completa con el sistema central **Super Base Madre** (UNS-Shatak).

## ✨ Nuevo: Integración con Base Madre

### ¿Qué es esto?

Esta versión incluye conexión directa al sistema central de empleados de Base Madre, permitiendo:

- 👤 **Buscar y seleccionar empleados** desde Base Madre en tus contratos
- 🏢 **Acceso a datos de empresas y plantas** en tiempo real
- 📊 **Información actualizada** de empleados (status, ubicación, salario)
- 🔍 **Búsqueda inteligente** por nombre, email o ID
- 💾 **Sin duplicación de datos** - Base Madre es la fuente de verdad

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos

- Node.js 18+
- API de Base Madre corriendo (UNS-Shatak)
- API Key de Base Madre

### 2. Configuración

```bash
cd frontend

# Copiar archivo de configuración
cp .env.local.example .env.local

# Editar y agregar tu API Key
nano .env.local
```

Configurar `.env.local`:

```bash
BASE_MADRE_API_URL=http://localhost:5000/api/v1
BASE_MADRE_API_KEY=tu_api_key_aqui
```

### 3. Instalar y Ejecutar

```bash
npm install
npm run dev
```

### 4. Probar la Integración

Visita: **http://localhost:3000/base-madre-test**

Esta página te permite probar todas las funcionalidades de integración.

---

## 📁 Nuevos Archivos Agregados

### Cliente API

```
frontend/lib/base-madre-client.ts
```

Cliente TypeScript para conectar con Base Madre API.

**Funciones:**
- `getEmployees()` - Listar empleados con paginación
- `getEmployee(id)` - Obtener empleado específico
- `searchEmployees(query)` - Buscar empleados
- `getCompanies()` - Listar empresas
- `getCompany(id)` - Detalles de empresa
- `getPlants(companyId?)` - Listar plantas
- `health()` - Health check

### React Hooks

```
frontend/hooks/use-base-madre.ts
```

Hooks personalizados para consumir Base Madre:

- `useEmployees()` - Lista de empleados con filtros
- `useEmployee(id)` - Empleado específico
- `useEmployeeSearch()` - Búsqueda con debounce
- `useCompanies()` - Lista de empresas
- `useCompany(id)` - Empresa específica
- `usePlants()` - Lista de plantas
- `useBaseMadreHealth()` - Estado de conexión

### Componentes UI

```
frontend/components/base-madre/
├── EmployeeSelector.tsx      # Selector con búsqueda
└── EmployeeDetailsCard.tsx   # Tarjeta de detalles
```

**EmployeeSelector:**
- Búsqueda en tiempo real con debounce
- Dropdown con lista reciente de empleados
- Filtro por empresa
- Solo empleados activos (在職中)
- Autocomplete inteligente

**EmployeeDetailsCard:**
- Muestra información completa del empleado
- Contacto (email, teléfono)
- Empresa y ubicación
- Información personal (nacionalidad, edad)
- Datos de visa
- Salario por hora

### Página de Test

```
frontend/app/base-madre-test/page.tsx
```

Página completa para probar la integración con 5 secciones:
1. Selector de empleados
2. Lista de empresas
3. Empleados recientes
4. Detalles del empleado
5. Plantas

---

## 🎯 Uso en Tus Contratos

### Integrar en Formulario de Contrato

```tsx
import { EmployeeSelector } from '@/components/base-madre/EmployeeSelector';
import { EmployeeDetailsCard } from '@/components/base-madre/EmployeeDetailsCard';
import { useState } from 'react';

export function ContractForm() {
  const [employeeId, setEmployeeId] = useState<number | null>(null);

  return (
    <div>
      <h2>Seleccionar Empleado</h2>

      {/* Selector */}
      <EmployeeSelector
        value={employeeId}
        onChange={(id, employee) => {
          setEmployeeId(id);
          console.log('Selected:', employee);
        }}
      />

      {/* Mostrar detalles */}
      {employeeId && (
        <EmployeeDetailsCard employeeId={employeeId} />
      )}
    </div>
  );
}
```

### Usar Hooks Directamente

```tsx
import { useEmployees } from '@/hooks/use-base-madre';

export function EmployeeList() {
  const { employees, loading, error } = useEmployees({
    status: '在職中',
    limit: 50,
  });

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <ul>
      {employees.map(emp => (
        <li key={emp.id}>{emp.name} - {emp.company_name}</li>
      ))}
    </ul>
  );
}
```

---

## 🔐 Seguridad

### API Key

El API Key se envía en el header `X-API-Key` en cada request:

```typescript
headers: {
  'X-API-Key': 'tu_api_key_aqui'
}
```

### Rate Limiting

Base Madre tiene límites de requests:
- Endpoints de lista: 100 requests/hora
- Endpoints de detalle: 200 requests/hora
- Health check: Sin límite

### Variables de Entorno

**Nunca** commitees tu API Key. Usa `.env.local`:

```bash
# ✅ Correcto - archivo ignorado por git
.env.local

# ❌ Incorrecto - NO commitear
.env
```

---

## 📊 Estructura de Datos

### Employee

```typescript
interface Employee {
  id: number;
  employee_id: string;
  name: string;
  name_kana?: string;
  email?: string;
  phone?: string;
  status: string;  // "在職中" | "退職" | "待機中"
  hire_date?: string;
  nationality?: string;
  gender?: string;
  age?: number;
  visa_type?: string;
  visa_expiry?: string;
  dispatch_company?: string;
  hourly_rate?: number;
  company_name?: string;
  company_id?: number;
  plant_name?: string;
  plant_id?: number;
  line_name?: string;
  production_line_id?: number;
}
```

### Company

```typescript
interface Company {
  id: number;
  company_name: string;
  address?: string;
  phone?: string;
  email?: string;
  contact_person?: string;
  contact_phone?: string;
  responsible_department?: string;
  plants_count: number;
  employees_count: number;
  jigyosho_count?: number;
}
```

### Plant

```typescript
interface Plant {
  id: number;
  plant_name: string;
  plant_code?: string;
  plant_address?: string;
  plant_phone?: string;
  manager_name?: string;
  company_name: string;
  company_id: number;
  jigyosho_name?: string;
  production_lines_count: number;
  employees_count: number;
}
```

---

## 🐛 Troubleshooting

### Error: "API Key not configured"

**Solución:**
1. Verificar que `.env.local` existe
2. Verificar que `BASE_MADRE_API_KEY` está configurada
3. Reiniciar el servidor de desarrollo (`npm run dev`)

### Error: "Cannot connect to Base Madre"

**Solución:**
1. Verificar que Base Madre está corriendo (`http://localhost:5000/api/v1/health`)
2. Verificar la URL en `.env.local`
3. Verificar CORS en Base Madre

### Error: "Rate limit exceeded"

**Solución:**
- Esperar 1 hora
- O contactar admin de Base Madre para aumentar límite

### No se muestran empleados

**Solución:**
1. Verificar que hay datos en Base Madre
2. Verificar filtros (status, company_id)
3. Revisar console del navegador para errores

---

## 📚 Documentación Adicional

- **Plan de Integración:** Ver `INTEGRATION_IMPLEMENTATION_PLAN.md` en UNS-Shatak
- **API Reference:** Ver `API_V1_TESTING_GUIDE.md` en UNS-Shatak
- **Base Madre Repo:** https://github.com/jokken79/UNS-Shatak

---

## 🎨 Características Técnicas

### Performance

- ✅ **Debounce** en búsqueda (300ms)
- ✅ **Lazy loading** de datos (enabled prop)
- ✅ **Paginación** eficiente
- ✅ **Cache** automático con React hooks

### UX

- ✅ **Estados de carga** con spinners
- ✅ **Manejo de errores** con mensajes claros
- ✅ **Búsqueda en tiempo real** con feedback visual
- ✅ **Responsive** - funciona en móvil y desktop
- ✅ **Accesibilidad** - soporte de teclado

### Tailwind CSS

Todos los componentes usan Tailwind CSS para estilos:
- No requiere CSS adicional
- Totalmente customizable
- Dark mode ready

---

## 🔄 Diferencias con el Original

Este fork incluye:

| Característica | Original | Integrado |
|----------------|----------|-----------|
| Datos de empleados | Local | Base Madre API |
| Búsqueda de empleados | No | ✅ Sí (tiempo real) |
| Información actualizada | No | ✅ Sí (siempre sincronizado) |
| Datos de empresas | Limitado | ✅ Completo con stats |
| Datos de plantas | No | ✅ Sí |
| Componentes reutilizables | No | ✅ Sí |
| Health monitoring | No | ✅ Sí |

---

## 🚧 Próximos Pasos

Ideas para mejorar:

1. **Cache offline** - Guardar datos localmente
2. **Webhooks** - Notificaciones de cambios
3. **Sync bidireccional** - Actualizar Base Madre desde Kobetsu
4. **Dashboard** - Estadísticas de uso de API
5. **Filtros avanzados** - Más opciones de búsqueda

---

## 👨‍💻 Desarrollo

### Agregar nuevos componentes

```bash
# Crear nuevo componente de Base Madre
touch frontend/components/base-madre/TuComponente.tsx
```

### Agregar nuevos hooks

```bash
# Editar hooks file
nano frontend/hooks/use-base-madre.ts
```

### Testing

```bash
# Ejecutar tests
npm test

# Test específico
npm test -- EmployeeSelector
```

---

## 📞 Soporte

Para problemas con:
- **Integración:** Revisar esta documentación
- **API de Base Madre:** Ver UNS-Shatak repo
- **Bugs:** Crear issue en GitHub

---

## 📄 Licencia

Same as original UNS-Kobetsu-Keiyakusho.

---

**Creado con ❤️ para conectar Kobetsu con Super Base Madre** 🚀
