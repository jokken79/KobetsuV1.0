# 🔄 Opción C: Modo Híbrido - Base Madre + Kobetsu

## ¿Qué es el Modo Híbrido?

El **Modo Híbrido** combina lo mejor de ambos mundos:

```
✅ Empleados: Base Madre API (Tiempo real, Single Source of Truth)
✅ Contratos: Kobetsu PostgreSQL (Local, Rápido, Independiente)
```

---

## 🎯 Cómo Funciona

### **Flujo de Trabajo**

```
┌──────────────────────────────────────────────────────────────┐
│                 CREACIÓN DE CONTRATO                         │
└──────────────────────────────────────────────────────────────┘

1. Usuario va a: /kobetsu/create

2. Formulario Híbrido se carga
   ├─ Conecta con Base Madre API
   ├─ Muestra indicador de conexión (verde/amarillo)
   └─ Carga fábricas desde Kobetsu local

3. Selección de Empleado
   ├─ Si Base Madre conectada:
   │  ├─ Usa EmployeeSelector (búsqueda en tiempo real)
   │  ├─ Busca en Base Madre API
   │  ├─ Muestra empleados activos (在職中)
   │  └─ Permite selección múltiple
   │
   └─ Si Base Madre desconectada:
      ├─ Muestra advertencia
      ├─ Cae back a empleados locales (si hay)
      └─ O muestra mensaje para conectar Base Madre

4. Al seleccionar empleado:
   ├─ Guarda ID del empleado de Base Madre
   ├─ Cachea datos en Kobetsu (nombre, email, salario)
   ├─ Muestra tarjeta con información
   └─ Permite agregar más empleados

5. Al crear contrato:
   ├─ Guarda contrato en PostgreSQL Kobetsu
   ├─ Guarda referencia: base_madre_employee_id
   ├─ Cachea datos del empleado localmente
   └─ Redirige a vista del contrato
```

---

## 📊 Ventajas del Modo Híbrido

| Característica | Ventaja |
|----------------|---------|
| **Datos actualizados** | Siempre obtiene info más reciente de empleados |
| **Sin duplicación** | No necesita copiar todos los empleados a Kobetsu |
| **Búsqueda rápida** | Búsqueda en tiempo real con debounce |
| **Offline ready** | Cache local permite trabajar sin Base Madre |
| **Independencia** | Contratos viven en Kobetsu, no dependen de Base Madre |
| **Performance** | Solo consulta Base Madre cuando es necesario |

---

## 🖥️ Interfaz de Usuario

### **Indicador de Conexión**

Al abrir `/kobetsu/create` verás un banner en la parte superior:

**✅ Conectado:**
```
┌────────────────────────────────────────────────────┐
│  ✅ Base Madre 接続済み                             │
│  従業員データはリアルタイムで取得されます             │
└────────────────────────────────────────────────────┘
```

**⚠️ Desconectado:**
```
┌────────────────────────────────────────────────────┐
│  ⚠️ Base Madre 未接続                              │
│  ローカルデータベースから従業員を選択します          │
└────────────────────────────────────────────────────┘
```

### **Selector de Empleado**

```
┌────────────────────────────────────────────────────┐
│  Buscar empleado por nombre, email o ID...        │
│  [                                            ] 🔍 │
└────────────────────────────────────────────────────┘
        │
        ↓ (Al escribir)
┌────────────────────────────────────────────────────┐
│  👤 山田太郎                                        │
│     EMP001 • Toyota Motor Corporation              │
│     ¥1,500/時 • 在職中                             │
├────────────────────────────────────────────────────┤
│  👤 田中花子                                        │
│     EMP002 • Toyota Motor Corporation              │
│     ¥1,400/時 • 在職中                             │
└────────────────────────────────────────────────────┘
```

### **Empleados Seleccionados**

```
選択された労働者 (2名)

┌────────────────────────────────────────────────────┐
│  👤  山田太郎                              [✕ 削除]│
│      ヤマダタロウ                                  │
│      ID: EMP001 • Toyota • ¥1,500/時               │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  👤  田中花子                              [✕ 削除]│
│      タナカハナコ                                  │
│      ID: EMP002 • Toyota • ¥1,400/時               │
└────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración

### **1. Iniciar Kobetsu (Backend + Frontend)**

```bash
cd /home/user/UNS-Kobetsu-Integrated

# Configurar
cp .env.example .env
nano .env  # Configurar SECRET_KEY y POSTGRES_PASSWORD

# Iniciar servicios
docker compose up -d

# Crear base de datos
docker exec -it uns-kobetsu-backend alembic upgrade head

# Crear admin
docker exec -it uns-kobetsu-backend python scripts/create_admin.py
```

**Acceder a:**
- Frontend: http://localhost:3010
- Backend API: http://localhost:8010/docs

### **2. Iniciar Base Madre (API)**

```bash
cd /home/user/UNS-Shatak/postgres_app

# Verificar que PostgreSQL está corriendo
# Luego iniciar API
python app.py
```

**Acceder a:**
- API: http://localhost:5000/api/v1/health

### **3. Configurar Conexión en Kobetsu**

```bash
cd /home/user/UNS-Kobetsu-Integrated/frontend

# Crear config
cp .env.local.example .env.local

# Editar
nano .env.local
```

**Agregar:**
```bash
BASE_MADRE_API_URL=http://localhost:5000/api/v1
BASE_MADRE_API_KEY=tu_api_key_generada_en_base_madre
```

**Reiniciar frontend:**
```bash
docker compose restart frontend
# O si estás en dev:
npm run dev
```

---

## 📝 Usar el Modo Híbrido

### **Paso 1: Login en Kobetsu**

1. Ir a: http://localhost:3010/login
2. Usuario: `admin`
3. Password: (el que configuraste)

### **Paso 2: Crear Contrato**

1. Click en **"Contratos"** en sidebar
2. Click en **"新規作成"** (Nuevo)
3. URL: http://localhost:3010/kobetsu/create

### **Paso 3: Verificar Conexión**

- ✅ Verde = Base Madre conectada
- ⚠️ Amarillo = Desconectada (usa datos locales)

### **Paso 4: Seleccionar Empleados**

1. En "労働者の選択" (Selección de empleados)
2. Escribe nombre, email, o ID del empleado
3. Aparecerá dropdown con resultados de Base Madre
4. Click en empleado para seleccionar
5. Se agrega a la lista de seleccionados
6. Repite para agregar más empleados

### **Paso 5: Completar Formulario**

1. Selecciona **"派遣先企業"** (Empresa destino)
2. Completa **"契約期間"** (Periodo del contrato)
3. Describe **"業務内容"** (Contenido del trabajo)
4. Click **"契約書を作成"** (Crear contrato)

### **Paso 6: Ver Contrato**

- Se redirige a `/kobetsu/{id}`
- Muestra contrato con datos de empleados
- Los datos del empleado vienen de Base Madre (si está conectada)
- O del cache local (si no está conectada)

---

## 🔄 Comportamiento Offline

### **Si Base Madre NO está disponible:**

```
1. Indicador muestra: ⚠️ Base Madre 未接続

2. Opciones:
   ├─ A) Conectar Base Madre y recargar página
   ├─ B) Usar datos cacheados de empleados previos
   └─ C) Usar sync tradicional desde Excel/JSON

3. Al crear contrato sin Base Madre:
   ├─ Usa datos del cache local (si existen)
   ├─ Guarda contrato normalmente en Kobetsu
   └─ Marca como "needs_sync" para actualizar después
```

### **Sincronización posterior:**

Cuando Base Madre vuelva a estar disponible:
```bash
# Manual: Visitar contrato y actualizar
# Automático: Script de sync (en desarrollo)
```

---

## 💾 Qué se Guarda Dónde

### **Base Madre (PostgreSQL - UNS-Shatak)**

```sql
-- Datos maestros de empleados
haken_shain:
  - id (PRIMARY KEY)
  - employee_id (社員№)
  - name, name_kana
  - email, phone
  - status, hire_date
  - company_id, plant_id
  - hourly_rate
  - visa_type, visa_expiry
  - ... (todos los datos del empleado)
```

**Responsabilidad:** Single Source of Truth para empleados

### **Kobetsu (PostgreSQL - UNS-Kobetsu-Integrated)**

```sql
-- Contratos individuales
kobetsu_keiyakusho:
  - id (PRIMARY KEY)
  - factory_id
  - contract_date
  - dispatch_start_date
  - dispatch_end_date
  - work_content
  - hourly_rate
  - ... (datos del contrato)

-- Relación contrato-empleado
kobetsu_employees:
  - id (PRIMARY KEY)
  - kobetsu_id (FK)
  - base_madre_employee_id  ← Referencia a Base Madre
  - cached_employee_name     ← Cache para offline
  - cached_employee_number   ← Cache para offline
  - cached_hourly_rate       ← Cache para offline
  - last_synced_at          ← Última actualización

-- Fábricas (pueden venir de Base Madre o sync local)
factories:
  - id (PRIMARY KEY)
  - company_name
  - plant_name
  - ... (datos de la fábrica)
```

**Responsabilidad:** Gestión de contratos y cache de datos

---

## 🔍 Debugging y Troubleshooting

### **Problema: No aparece nada al buscar empleado**

**Soluciones:**
```bash
# 1. Verificar Base Madre
curl http://localhost:5000/api/v1/health

# 2. Verificar API Key
# En frontend/.env.local
echo $BASE_MADRE_API_KEY

# 3. Ver console del navegador
# F12 → Console → buscar errores

# 4. Verificar que hay empleados activos
curl -H "X-API-Key: TU_KEY" \
  http://localhost:5000/api/v1/employees?status=在職中
```

### **Problema: Indicador amarillo (desconectado)**

**Causas comunes:**
1. Base Madre no está corriendo
2. URL incorrecta en `.env.local`
3. API Key incorrecta o expirada
4. CORS no configurado en Base Madre

**Solución:**
```bash
# Verificar Base Madre
cd /home/user/UNS-Shatak/postgres_app
python app.py

# Verificar en navegador
http://localhost:5000/api/v1/health

# Debe retornar:
# {"status": "healthy", "service": "UNS Base Madre", ...}
```

### **Problema: Error al crear contrato**

**Ver logs:**
```bash
# Backend Kobetsu
docker logs uns-kobetsu-backend -f

# Frontend Kobetsu
docker logs uns-kobetsu-frontend -f

# Base Madre
# En terminal donde corre python app.py
```

---

## 📈 Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA HÍBRIDA                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐                    ┌────────────────────────┐
│  Base Madre API  │◄───────────────────┤  Kobetsu Frontend      │
│  (UNS-Shatak)    │                    │  (React/Next.js)       │
│                  │  HTTP GET          │                        │
│  PostgreSQL 15   │  /api/v1/employees │  - EmployeeSelector    │
│  - haken_shain   │  X-API-Key         │  - KobetsuFormHybrid   │
│  - companies     │                    │  - useBaseMadreHealth  │
│  - plants        │                    │                        │
└──────────────────┘                    └────────┬───────────────┘
                                                 │
                                                 │ HTTP POST
                                                 │ /api/v1/kobetsu
                                                 │
                                        ┌────────▼───────────────┐
                                        │  Kobetsu Backend       │
                                        │  (FastAPI)             │
                                        │                        │
                                        │  - kobetsuApi.create() │
                                        │  - Validation          │
                                        │  - Business logic      │
                                        └────────┬───────────────┘
                                                 │
                                                 │ INSERT
                                                 │
                                        ┌────────▼───────────────┐
                                        │  Kobetsu PostgreSQL    │
                                        │                        │
                                        │  - kobetsu_keiyakusho  │
                                        │  - kobetsu_employees   │
                                        │  - factories           │
                                        └────────────────────────┘

DATOS GUARDADOS:
- base_madre_employee_id: 123 (referencia)
- cached_employee_name: "山田太郎" (cache)
- cached_hourly_rate: 1500 (cache)
```

---

## 🎓 Mejores Prácticas

### **1. Siempre usar Base Madre cuando esté disponible**

✅ **CORRECTO:**
```typescript
// Al crear contrato, buscar en Base Madre
const employee = await baseMadreClient.getEmployee(employeeId);
// Usar datos frescos de Base Madre
```

❌ **INCORRECTO:**
```typescript
// Usar solo cache sin verificar Base Madre
const employee = cachedEmployees.find(e => e.id === employeeId);
```

### **2. Actualizar cache periódicamente**

```bash
# Ejecutar script de sync (cuando esté disponible)
docker exec -it uns-kobetsu-backend python scripts/sync_base_madre.py
```

### **3. Monitorear conexión**

- Verificar indicador verde al crear contratos
- Si está amarillo, investigar causa antes de crear muchos contratos

### **4. Backup regular**

```bash
# Backup Kobetsu (contratos)
docker exec -it uns-kobetsu-postgres pg_dump -U kobetsu_admin kobetsu_db > backup.sql

# Backup Base Madre (empleados)
# Ver documentación de Base Madre
```

---

## 🚀 Próximas Mejoras

### **Fase 1: Implementado ✅**
- [x] EmployeeSelector con Base Madre
- [x] KobetsuFormHybrid
- [x] Indicador de conexión
- [x] Cache básico de empleados
- [x] Selección múltiple

### **Fase 2: En desarrollo 🔄**
- [ ] Sync automático de cache
- [ ] Vista de contrato con datos de Base Madre
- [ ] Indicador de "datos desactualizados"
- [ ] Botón "Actualizar desde Base Madre"

### **Fase 3: Futuro 📅**
- [ ] Webhooks de Base Madre para actualizaciones push
- [ ] Sync bidireccional (actualizar Base Madre desde Kobetsu)
- [ ] Dashboard de sincronización
- [ ] Histórico de cambios

---

## 📞 Soporte

**Problemas con:**
- **Base Madre:** Ver `UNS-Shatak/API_V1_TESTING_GUIDE.md`
- **Kobetsu:** Ver `INTEGRATION_README.md`
- **Conexión:** Revisar esta guía sección "Debugging"

---

**¡El Modo Híbrido está listo para usar!** 🎉

Tu workflow ahora es:
1. Abrir Kobetsu → Crear Contrato
2. Buscar empleado en Base Madre (tiempo real)
3. Seleccionar y completar formulario
4. Guardar en Kobetsu
5. ✅ Contrato creado con datos actualizados

**Sin duplicación, sin complejidad, todo integrado.** 🚀
