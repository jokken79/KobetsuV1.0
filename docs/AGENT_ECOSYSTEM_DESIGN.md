# Ecosistema de Agentes para UNS-Kobetsu
## Arquitectura Completa de Agentes IA para Gestión de 個別契約書

**Fecha:** 2025-12-07
**Versión:** 1.0
**Autor:** Arquitecto de Agentes IA

---

## 1. Resumen Ejecutivo de la Aplicación

### ¿Qué es UNS-Kobetsu?

**UNS-Kobetsu** es un sistema integral de gestión de **個別契約書** (contratos individuales de dispatch de personal) diseñado para cumplir con la **労働者派遣法第26条** (Ley de Dispatch Laboral de Japón, Artículo 26).

El sistema reemplaza un sistema Excel legacy con **11,000+ fórmulas**, **18 hojas interconectadas**, **1,028 empleados** y **111 configuraciones de fábricas**.

### Usuarios Principales

| Tipo de Usuario | Rol | Acciones Principales |
|-----------------|-----|---------------------|
| **Administrador de Contratos** | Gestiona 個別契約書 | Crear, editar, renovar contratos |
| **Gerente de RRHH** | Supervisa empleados y asignaciones | Asignar empleados a fábricas |
| **Ejecutivo** | Visión ejecutiva | Dashboard, estadísticas, reportes |
| **Operador de Datos** | Importación/Exportación | Sincronizar datos con Excel |
| **Auditor Legal** | Cumplimiento | Verificar 16 campos legales obligatorios |

### Valor de Negocio

1. **Cumplimiento Legal**: Garantiza los 16 campos requeridos por 労働者派遣法第26条
2. **Automatización**: Reemplaza procesos manuales de Excel con 11,000+ fórmulas
3. **Generación de Documentos**: PDF/DOCX automatizados para 9 tipos de documentos
4. **Trazabilidad**: Historial completo de contratos y asignaciones
5. **Alertas Proactivas**: Notificación de contratos próximos a vencer

---

## 2. Mapa Funcional por Áreas

### 2.1 Gestión de Contratos (個別契約書)

| Problema que Resuelve | Acciones del Usuario | Datos Críticos |
|----------------------|---------------------|----------------|
| Crear contratos con 16 campos legales | Llenar formulario, seleccionar fábrica/empleados | work_content, supervisor, work_days |
| Renovar contratos próximos a vencer | Clic en "Renovar", ajustar fechas | dispatch_start_date, dispatch_end_date |
| Generar documentos oficiales | Descargar PDF/DOCX | Todos los 16 campos legales |
| Buscar y filtrar contratos | Filtrar por fábrica, estado, fechas | factory_id, status, date_range |

**Oportunidad A**: Agente que valide automáticamente cumplimiento de 16 campos legales antes de generar documentos.

### 2.2 Gestión de Fábricas (派遣先)

| Problema que Resuelve | Acciones del Usuario | Datos Críticos |
|----------------------|---------------------|----------------|
| Mantener catálogo de clientes | CRUD de fábricas | company_name, factory_name, line |
| Configurar horarios y descansos | Editar breaks, shifts | break_minutes, shift_premium |
| Asignar líneas de producción | Gestionar production_lines | line_name, supervisor |

**Oportunidad B**: Agente que detecte inconsistencias entre configuración de fábrica y contratos activos.

### 2.3 Gestión de Empleados (派遣社員)

| Problema que Resuelve | Acciones del Usuario | Datos Críticos |
|----------------------|---------------------|----------------|
| Mantener registro de empleados | CRUD de empleados | employee_number, full_name, status |
| Asignar a contratos | Seleccionar empleados al crear contrato | employee_ids, factory_id |
| Sincronizar con Excel | Importar desde DBGenzai | 派遣先 mapping |

**Oportunidad C**: Agente que sugiera empleados disponibles según habilidades y ubicación.

### 2.4 Generación de Documentos

| Documento | Base Legal | Estado |
|-----------|-----------|--------|
| 個別契約書 (Contrato Individual) | 労働者派遣法第26条 | ✅ Implementado |
| 通知書 (Notificación) | 労働者派遣法第35条 | ✅ Implementado |
| 派遣先管理台帳 (Registro Cliente) | - | ✅ Implementado |
| 派遣元管理台帳 (Registro Origen) | - | ✅ Implementado |
| 派遣時の待遇情報明示書 | 法31条の2第3項 | ✅ Implementado |
| 労働契約書 兼 就業条件明示書 | - | ⚠️ Parcial |
| 雇入れ時の待遇情報明示書 | 法31条の2第2項 | ✅ Implementado |
| 就業状況報告書 | - | ✅ Implementado |

**Oportunidad D**: Agente que genere automáticamente todos los documentos requeridos al crear un contrato.

### 2.5 Importación y Sincronización

| Fuente | Datos | Método |
|--------|-------|--------|
| Excel (DBGenzai) | 1,028 empleados | import_service.py |
| Excel (TBKaisha) | 111 fábricas | import_service.py |
| JSON (factories/) | Configuraciones | sync_service.py |

**Oportunidad E**: Agente que detecte y resuelva conflictos de sincronización automáticamente.

### 2.6 Dashboard y Analítica

| Métrica | Endpoint | Uso |
|---------|----------|-----|
| Contratos activos | /kobetsu/stats | Dashboard principal |
| Próximos a vencer | /kobetsu?expiring_within_days=30 | Alertas |
| Por fábrica | /kobetsu?factory_id=X | Filtros |
| Empleados asignados | /kobetsu/{id}/employees | Detalle |

**Oportunidad F**: Agente que genere reportes ejecutivos automatizados con insights.

---

## 3. Oportunidades para Agentes de IA

| ID | Oportunidad | Tipo | Impacto | Prioridad |
|----|-------------|------|---------|-----------|
| **A** | Validación de cumplimiento legal (16 campos) | Validación | Alto | 🔴 Alta |
| **B** | Detección de inconsistencias fábrica-contrato | Análisis | Medio | 🟡 Media |
| **C** | Sugerencia de empleados disponibles | Recomendación | Medio | 🟡 Media |
| **D** | Generación automática de documentos | Automatización | Alto | 🔴 Alta |
| **E** | Resolución de conflictos de sincronización | ETL | Medio | 🟡 Media |
| **F** | Reportes ejecutivos con insights | Analítica | Alto | 🔴 Alta |
| **G** | Alertas proactivas de vencimientos | Notificación | Alto | 🔴 Alta |
| **H** | Traducción/localización Japonés-Español | NLP | Bajo | 🟢 Baja |
| **I** | Análisis de patrones de contratos | ML/Analytics | Medio | 🟡 Media |

---

## 4. Auditoría de Agentes Existentes

### 4.1 Inventario de Agentes Actuales (26 agentes)

#### Agentes Core (8)

| Agente | Modelo | Objetivo | Fortalezas | Debilidades | Riesgo |
|--------|--------|----------|------------|-------------|--------|
| **planner** | opus | Planificación estratégica de tareas | Muy detallado, context-aware | Puede over-engineer | Bajo |
| **architect** | opus | Diseño de sistema | Visión holística | No conoce dominio específico | Medio |
| **critic** | opus | Validar decisiones | Previene errores | Puede ser demasiado conservador | Bajo |
| **explorer** | opus | Investigar código | Muy thorough | Puede ser lento | Bajo |
| **memory** | opus | Contexto persistente | Mantiene continuidad | Archivo puede crecer mucho | Bajo |
| **coder** | sonnet | Implementación | Rápido, efectivo | No conoce reglas de negocio | Medio |
| **tester** | sonnet | Verificación | Riguroso | Solo tests técnicos | Medio |
| **stuck** | sonnet | Escalación humana | Previene errores críticos | Puede bloquear progreso | Bajo |

#### Agentes de Calidad (4)

| Agente | Modelo | Objetivo | Fortalezas | Debilidades | Riesgo |
|--------|--------|----------|------------|-------------|--------|
| **security** | opus | Auditoría de seguridad | OWASP Top 10, CVE | No conoce compliance japonés | Medio |
| **debugger** | opus | Investigar bugs | Root cause analysis | Requiere reproducción | Bajo |
| **reviewer** | opus | Calidad de código | Mejora mantenibilidad | Puede ser subjetivo | Bajo |
| **performance** | opus | Optimización | Detecta bottlenecks | Requiere métricas claras | Bajo |

#### Agentes de Dominio (7+)

| Agente | Modelo | Objetivo | Fortalezas | Debilidades | Riesgo |
|--------|--------|----------|------------|-------------|--------|
| **frontend** | opus | UI/UX React/Next.js | Patrones modernos | No conoce UX japonés | Bajo |
| **backend** | opus | FastAPI/Python | Arquitectura limpia | No conoce lógica de contratos | Medio |
| **database** | opus | PostgreSQL/SQLAlchemy | Schema design | No conoce modelo de negocio | Medio |
| **data-sync** | opus | Migración Excel→DB | Patrones ETL | No conoce formato Excel específico | Medio |
| **excel-migrator** | sonnet | Análisis Excel | Conoce estructura Excel | Solo migración, no operación | Bajo |
| **devops** | opus | Docker/CI/CD | Infraestructura | No conoce requisitos producción | Bajo |
| **api-designer** | opus | OpenAPI/REST | Best practices | No conoce endpoints específicos | Bajo |

#### Agentes Adicionales (7)

| Agente | Modelo | Objetivo | Estado |
|--------|--------|----------|--------|
| **migrator** | opus | Transiciones seguras | Activo |
| **docs-writer** | opus | Documentación | Activo |
| **documenter** | opus | Auto-documentación | Activo |
| **playwright** | sonnet | E2E testing | Activo |
| **detective** | opus | Investigación profunda | Activo |
| **api** | opus | Diseño REST | Activo |

### 4.2 Análisis de Cobertura

```
                    COBERTURA DEL SISTEMA

    ┌─────────────────────────────────────────────────┐
    │                 ORQUESTADOR                      │
    │            (Claude 200k context)                 │
    └─────────────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐         ┌─────────┐         ┌─────────┐
│TÉCNICO  │         │PROCESO  │         │NEGOCIO  │
│ ✅ 85%  │         │ ✅ 90%  │         │ ⚠️ 30%  │
└─────────┘         └─────────┘         └─────────┘
    │                   │                   │
    ├─ frontend ✅      ├─ planner ✅       ├─ ??? ❌
    ├─ backend ✅       ├─ coder ✅         ├─ ??? ❌
    ├─ database ✅      ├─ tester ✅        ├─ ??? ❌
    ├─ security ✅      ├─ reviewer ✅      └─ ??? ❌
    ├─ devops ✅        ├─ debugger ✅
    └─ performance ✅   └─ stuck ✅
```

**Conclusión**: Excelente cobertura técnica y de proceso, pero **MUY BAJA cobertura de dominio de negocio**.

---

## 5. Arquitectura Propuesta del Ecosistema de Agentes

### 5.1 Arquitectura General

```
                    ┌─────────────────────────────────────────┐
                    │           ORQUESTADOR CLAUDE            │
                    │          (200k context window)          │
                    │                                         │
                    │  • Mantiene visión del proyecto         │
                    │  • Delega tareas a agentes              │
                    │  • Verifica resultados                  │
                    │  • Actualiza memoria                    │
                    └─────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   AGENTES     │           │   AGENTES     │           │   AGENTES     │
│   TÉCNICOS    │           │   PROCESO     │           │   NEGOCIO     │
│               │           │               │           │   (NUEVOS)    │
├───────────────┤           ├───────────────┤           ├───────────────┤
│ • frontend    │           │ • planner     │           │ • contract-   │
│ • backend     │           │ • coder       │           │   validator   │
│ • database    │           │ • tester      │           │ • document-   │
│ • security    │           │ • reviewer    │           │   generator   │
│ • devops      │           │ • debugger    │           │ • compliance  │
│ • performance │           │ • stuck       │           │ • analytics   │
│ • data-sync   │           │ • memory      │           │ • sync-       │
│ • api-designer│           │ • critic      │           │   resolver    │
└───────────────┘           └───────────────┘           └───────────────┘
        │                             │                             │
        └─────────────────────────────┴─────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │     AGENTE MONITOR DE CAMBIOS     │
                    │                                   │
                    │  • Detecta cambios en la app      │
                    │  • Propone ajustes a agentes      │
                    │  • Mantiene sincronía             │
                    └───────────────────────────────────┘
```

### 5.2 Comunicación entre Agentes

```
Flujo de Creación de Contrato:

Usuario → Orquestador → planner
                           │
                           ▼
                    contract-validator  ─────┐
                           │                 │
                           ▼                 │
                    backend (coder)          │ Paralelo
                           │                 │
                           ▼                 │
                    document-generator ──────┘
                           │
                           ▼
                       tester
                           │
                           ▼
                    compliance-checker
                           │
                           ▼
                       memory
```

---

## 6. Fichas Detalladas de Agentes Propuestos

### 6.1 Agente: CONTRACT-VALIDATOR (NUEVO)

```yaml
nombre: contract-validator
tipo: Especialista de Dominio / Validación
modelo: opus
rol_objetivo: |
  Validar que los contratos 個別契約書 cumplan con los 16 campos
  requeridos por 労働者派遣法第26条 antes de su creación o
  modificación. Prevenir contratos incompletos o ilegales.

responsabilidades:
  R1: Validar presencia de los 16 campos legales obligatorios
  R2: Verificar coherencia de fechas (inicio < fin, duraciones válidas)
  R3: Validar que la fábrica tenga configuración completa
  R4: Verificar que los empleados asignados estén disponibles
  R5: Detectar conflictos de horarios entre contratos

entradas:
  - Datos del contrato a validar (KobetsuCreate schema)
  - Información de la fábrica asociada
  - Lista de empleados a asignar
  - Contratos existentes del mismo período

salidas:
  - ValidationResult con status (valid/invalid)
  - Lista de errores encontrados con código y descripción
  - Lista de advertencias (warnings)
  - Sugerencias de corrección

fuentes_datos:
  - backend/app/models/kobetsu_keiyakusho.py
  - backend/app/schemas/kobetsu.py
  - Database: kobetsu_keiyakusho, factories, employees

interacciones:
  llama_a:
    - database: Para consultar contratos existentes
    - stuck: Cuando encuentra ambigüedad legal
  llamado_por:
    - planner: Al inicio de creación de contrato
    - backend: Durante validación de endpoint

criterios_exito:
  - 100% de contratos validados antes de creación
  - 0 contratos guardados sin los 16 campos
  - < 1% falsos positivos en validación

prompts_ejemplo:
  - "Valida el siguiente contrato para fábrica 高雄工業 岡山工場 con fechas 2025-01-01 a 2025-12-31"
  - "Verifica si los empleados [101, 102, 103] pueden ser asignados al contrato KOB-202501-0001"
  - "Detecta conflictos de horario para empleado 山田太郎 en el período enero-marzo 2025"
```

### 6.2 Agente: DOCUMENT-GENERATOR (NUEVO)

```yaml
nombre: document-generator
tipo: Especialista de Dominio / Automatización
modelo: opus
rol_objetivo: |
  Generar automáticamente todos los documentos legales requeridos
  (PDF/DOCX) a partir de un contrato 個別契約書. Garantiza formato
  oficial japonés y contenido completo.

responsabilidades:
  R1: Generar 個別契約書 (Contrato Individual)
  R2: Generar 通知書 (Notificación al cliente)
  R3: Generar 派遣先管理台帳 (Registro del cliente)
  R4: Generar 派遣元管理台帳 (Registro de origen)
  R5: Generar 就業条件明示書 (Condiciones de empleo)
  R6: Coordinar generación masiva de documentos

entradas:
  - ID del contrato o datos completos
  - Formato deseado (PDF, DOCX, ambos)
  - Tipo de documento específico o "todos"
  - Parámetros de personalización (idioma, membrete)

salidas:
  - Archivos generados (bytes o rutas)
  - Metadatos de los documentos
  - Log de generación
  - Errores si los hay

fuentes_datos:
  - backend/app/services/kobetsu_pdf_service.py
  - backend/app/services/kobetsu_excel_generator.py
  - backend/app/services/dispatch_documents_service.py
  - Templates en /app/templates/

interacciones:
  llama_a:
    - contract-validator: Valida antes de generar
    - backend: Para obtener datos del contrato
  llamado_por:
    - planner: Después de crear contrato
    - frontend: Cuando usuario solicita documentos

criterios_exito:
  - Documentos abren sin errores en Excel/Word
  - 100% de datos del contrato reflejados
  - Formato idéntico al Excel original
  - Tiempo de generación < 5 segundos por documento

prompts_ejemplo:
  - "Genera todos los documentos para el contrato KOB-202501-0001"
  - "Genera solo 個別契約書 en formato PDF para la fábrica 高雄工業"
  - "Genera documentos masivos para todos los contratos activos de enero 2025"
```

### 6.3 Agente: COMPLIANCE-CHECKER (NUEVO)

```yaml
nombre: compliance-checker
tipo: Especialista de Dominio / Auditoría Legal
modelo: opus
rol_objetivo: |
  Auditar el sistema para garantizar cumplimiento con
  労働者派遣法第26条 y otras regulaciones laborales japonesas.
  Detectar violaciones antes de que se conviertan en problemas legales.

responsabilidades:
  R1: Auditar contratos existentes por cumplimiento
  R2: Verificar que todas las fábricas tengan información completa
  R3: Detectar contratos vencidos que siguen activos
  R4: Alertar sobre empleados sin documentación actualizada
  R5: Generar reportes de cumplimiento para auditorías

entradas:
  - Rango de fechas para auditoría
  - Fábrica específica o todas
  - Tipo de auditoría (contratos, empleados, fábricas)
  - Nivel de detalle (resumen, completo)

salidas:
  - Reporte de cumplimiento con score (0-100)
  - Lista de violaciones categorizadas por severidad
  - Plan de remediación sugerido
  - Documentación para auditorías externas

fuentes_datos:
  - Database: todas las tablas principales
  - docs/LEGAL.md: Referencia de campos legales
  - Configuración de la empresa

interacciones:
  llama_a:
    - database: Consultas de auditoría
    - contract-validator: Validación individual
    - stuck: Cuando encuentra violación crítica
  llamado_por:
    - planner: En auditorías programadas
    - security: Durante auditoría de seguridad

criterios_exito:
  - Detectar 100% de violaciones de los 16 campos
  - Cero falsos negativos en auditorías
  - Reportes generados en < 30 segundos
  - Score de cumplimiento correlaciona con realidad

prompts_ejemplo:
  - "Audita todos los contratos activos por cumplimiento de 労働者派遣法第26条"
  - "Genera reporte de cumplimiento para fábrica コーリツ para auditoría externa"
  - "Identifica todos los contratos que vencen en los próximos 30 días sin renovación"
```

### 6.4 Agente: ANALYTICS-REPORTER (NUEVO)

```yaml
nombre: analytics-reporter
tipo: Especialista de Dominio / Analítica
modelo: opus
rol_objetivo: |
  Generar insights y reportes analíticos sobre contratos,
  empleados y fábricas. Detectar patrones, tendencias y
  anomalías para apoyar decisiones ejecutivas.

responsabilidades:
  R1: Generar dashboard de métricas clave
  R2: Analizar tendencias de contratos por período
  R3: Detectar anomalías en datos (outliers)
  R4: Predecir carga de trabajo por renovaciones
  R5: Comparar rendimiento entre fábricas

entradas:
  - Período de análisis
  - Métricas específicas o todas
  - Nivel de agregación (día, semana, mes)
  - Filtros (fábrica, departamento, estado)

salidas:
  - Dashboard JSON con métricas
  - Gráficos y visualizaciones (datos)
  - Insights en texto natural
  - Alertas de anomalías detectadas

fuentes_datos:
  - Database: todas las tablas
  - Histórico de cambios
  - Configuración de KPIs

interacciones:
  llama_a:
    - database: Queries analíticas
    - compliance-checker: Score de cumplimiento
  llamado_por:
    - planner: Para reportes ejecutivos
    - frontend: Para dashboard

criterios_exito:
  - Insights accionables y específicos
  - Precisión > 95% en predicciones
  - Tiempo de generación < 10 segundos
  - Detección temprana de problemas

prompts_ejemplo:
  - "Genera reporte ejecutivo de Q4 2024 para presentación a dirección"
  - "Analiza tendencia de renovaciones vs. terminaciones último año"
  - "Detecta fábricas con tasa anormal de rotación de empleados"
```

### 6.5 Agente: SYNC-RESOLVER (NUEVO)

```yaml
nombre: sync-resolver
tipo: Especialista de Dominio / ETL
modelo: opus
rol_objetivo: |
  Resolver conflictos de sincronización entre el sistema web
  y fuentes externas (Excel, JSON). Garantizar integridad de
  datos durante importaciones y actualizaciones.

responsabilidades:
  R1: Detectar conflictos durante sincronización
  R2: Proponer resolución automática o manual
  R3: Mantener log de cambios sincronizados
  R4: Validar datos antes de importar
  R5: Revertir sincronizaciones problemáticas

entradas:
  - Archivo fuente (Excel, CSV, JSON)
  - Tipo de entidad (employees, factories)
  - Estrategia de conflicto (overwrite, skip, ask)
  - Modo (dry-run, commit)

salidas:
  - Reporte de sincronización
  - Lista de conflictos con opciones
  - Datos sincronizados (si commit)
  - Rollback script (si necesario)

fuentes_datos:
  - Excel: DBGenzai, TBKaisha
  - JSON: factories/*.json
  - Database: employees, factories

interacciones:
  llama_a:
    - data-sync: Ejecutar sincronización técnica
    - database: Verificar estado actual
    - stuck: Cuando conflicto requiere decisión humana
  llamado_por:
    - planner: En tareas de importación
    - excel-migrator: Después de análisis

criterios_exito:
  - 0 pérdida de datos durante sync
  - 100% de conflictos identificados
  - Tiempo de sync < 2 minutos para 1000 registros
  - Rollback exitoso si hay problemas

prompts_ejemplo:
  - "Sincroniza empleados desde 個別契約書TEXPERT2025.xlsx detectando conflictos"
  - "Resuelve conflicto: empleado 山田太郎 tiene派遣先 diferente en Excel vs DB"
  - "Ejecuta dry-run de importación de fábricas desde TBKaisha"
```

### 6.6 Agente: ALERT-MANAGER (NUEVO)

```yaml
nombre: alert-manager
tipo: Especialista de Dominio / Notificaciones
modelo: sonnet
rol_objetivo: |
  Gestionar alertas proactivas sobre eventos críticos:
  contratos por vencer, empleados sin asignación,
  fábricas con datos incompletos, etc.

responsabilidades:
  R1: Monitorear contratos próximos a vencer (30, 15, 7 días)
  R2: Detectar empleados sin contrato activo
  R3: Alertar sobre fábricas con configuración incompleta
  R4: Notificar sobre anomalías detectadas
  R5: Generar resumen diario/semanal de alertas

entradas:
  - Configuración de umbrales (días antes de vencimiento)
  - Canales de notificación (email, dashboard, log)
  - Prioridad de alertas (crítica, alta, media, baja)
  - Frecuencia de monitoreo

salidas:
  - Lista de alertas activas con metadata
  - Notificaciones formateadas
  - Historial de alertas
  - Métricas de alertas (resueltas, pendientes)

fuentes_datos:
  - Database: contratos, empleados, fábricas
  - Configuración de alertas
  - Historial de notificaciones

interacciones:
  llama_a:
    - database: Queries de monitoreo
    - compliance-checker: Verificar cumplimiento
  llamado_por:
    - planner: En tareas programadas
    - Cron/Scheduler: Automáticamente

criterios_exito:
  - 0 contratos vencidos sin alerta previa
  - 100% de alertas críticas notificadas
  - < 5% de falsos positivos
  - Tiempo de detección < 1 hora

prompts_ejemplo:
  - "Lista todos los contratos que vencen en los próximos 30 días"
  - "Genera resumen de alertas para el dashboard de hoy"
  - "Identifica empleados activos sin contrato vigente"
```

---

## 7. Agentes Faltantes y Mejoras

### 7.1 Agentes que Faltan (Nuevos)

| Agente | Oportunidad | Prioridad | Esfuerzo | Impacto |
|--------|-------------|-----------|----------|---------|
| **contract-validator** | A | 🔴 Alta | Medio | Alto |
| **document-generator** | D | 🔴 Alta | Medio | Alto |
| **compliance-checker** | A | 🔴 Alta | Alto | Muy Alto |
| **analytics-reporter** | F | 🟡 Media | Medio | Alto |
| **sync-resolver** | E | 🟡 Media | Medio | Medio |
| **alert-manager** | G | 🔴 Alta | Bajo | Alto |

### 7.2 Mejoras a Agentes Existentes

| Agente | Mejora Propuesta | Prioridad |
|--------|-----------------|-----------|
| **backend** | Agregar conocimiento de los 16 campos legales | Alta |
| **frontend** | Agregar patrones de UX japonés (入力ガイド) | Media |
| **database** | Agregar validaciones de integridad para contratos | Alta |
| **security** | Agregar checklist de cumplimiento 個人情報保護法 | Media |
| **data-sync** | Integrar con sync-resolver para manejo de conflictos | Alta |
| **tester** | Agregar tests de cumplimiento legal | Alta |

### 7.3 Priorización de Implementación

#### Fase 1: Críticos (Sprint 1-2)
1. **contract-validator** - Previene contratos ilegales
2. **alert-manager** - Previene vencimientos ignorados
3. **compliance-checker** - Auditoría continua

#### Fase 2: Importantes (Sprint 3-4)
4. **document-generator** - Automatización de documentos
5. **sync-resolver** - Migración sin pérdida de datos

#### Fase 3: Mejoras (Sprint 5+)
6. **analytics-reporter** - Insights ejecutivos
7. Mejoras a agentes existentes

---

## 8. Agente Monitor de Cambios en la App

### 8.1 Definición

```yaml
nombre: app-change-monitor
tipo: Meta-Agente / Monitoreo
modelo: opus
rol: |
  Leer texto libre sobre cambios en la app (notas de versión,
  mensajes del equipo, tickets, documentación) y detectar qué
  partes del sistema cambian y qué agentes se ven afectados.
  Proponer acciones sobre los agentes (crear, modificar, eliminar).

entradas:
  - Texto libre describiendo cambios (commits, PRs, notas)
  - Lista actual de agentes (opcional)
  - Contexto del proyecto

salidas_estructuradas:
  cambios_detectados:
    - cambio_id: 1
      descripcion: "Nueva tabla factory_breaks para múltiples descansos"
      area_afectada: "Database / Factory Management"
      tipo_cambio: "nueva_funcionalidad"
      archivos_mencionados:
        - backend/app/models/factory.py
        - backend/app/schemas/factory.py

  impacto_en_agentes:
    - cambio_id: 1
      agentes_afectados:
        - agente: "database"
          tipo_impacto: "revisar"
          accion: "Agregar conocimiento de tabla factory_breaks"
        - agente: "backend"
          tipo_impacto: "modificar"
          accion: "Actualizar patrones para CRUD de breaks"
      agentes_nuevos_sugeridos:
        - nombre: "break-manager"
          rol: "Gestionar configuración de descansos por fábrica"
          prioridad: "baja"

reglas_funcionamiento:
  - Ser conservador: no inventar impactos sin relación clara
  - Si cambio no afecta agentes, indicarlo explícitamente
  - Si texto es ambiguo, señalar y pedir aclaraciones
  - Priorizar cambios que afectan lógica de negocio
```

### 8.2 Ejemplo de Uso

**Entrada (texto libre):**
```
Commit: feat: Multi-document template service

## Changes
- Added factory_breaks table for multiple breaks per factory
- Support for 昼勤, 夜勤, 残業時 break configurations
- New CRUD API endpoints for factory breaks
- Frontend UI for viewing/editing breaks on /factories page
```

**Salida del Monitor:**
```yaml
cambios_detectados:
  - cambio_1:
      descripcion: "Sistema de múltiples tiempos de descanso por fábrica"
      area: "Factory Management / Scheduling"
      tipo: "nueva_funcionalidad"

impacto_agentes:
  - database:
      impacto: "REVISAR"
      accion: "Agregar modelo FactoryBreak al conocimiento del agente"

  - backend:
      impacto: "MODIFICAR"
      accion: "Documentar nuevos endpoints /factories/{id}/breaks"

  - frontend:
      impacto: "REVISAR"
      accion: "Actualizar patrones de UI para sección de breaks"

  - contract-validator:
      impacto: "MODIFICAR"
      accion: "Validar que break_duration coincida con factory_breaks"

agentes_nuevos_sugeridos: null
# No se requieren nuevos agentes, funcionalidad cubierta por existentes
```

---

## 9. Plan de Implementación por Fases

### Fase 1: Fundamentos (2 semanas)

| Tarea | Agente | Entregable |
|-------|--------|------------|
| Crear contract-validator | coder | .claude/agents/contract-validator.md |
| Crear alert-manager | coder | .claude/agents/alert-manager.md |
| Mejorar backend con 16 campos | backend | Documentación actualizada |
| Tests de cumplimiento | tester | tests/test_compliance.py |

### Fase 2: Automatización (2 semanas)

| Tarea | Agente | Entregable |
|-------|--------|------------|
| Crear document-generator | coder | .claude/agents/document-generator.md |
| Crear compliance-checker | coder | .claude/agents/compliance-checker.md |
| Integrar sync-resolver | data-sync | Mejora en import_service.py |

### Fase 3: Analítica (1 semana)

| Tarea | Agente | Entregable |
|-------|--------|------------|
| Crear analytics-reporter | coder | .claude/agents/analytics-reporter.md |
| Dashboard de métricas | frontend | Nuevo componente |

### Fase 4: Monitoreo (1 semana)

| Tarea | Agente | Entregable |
|-------|--------|------------|
| Crear app-change-monitor | coder | .claude/agents/app-change-monitor.md |
| Integrar con CI/CD | devops | GitHub Action |

---

## 10. Apéndice: Campos Legales 労働者派遣法第26条

Los 16 campos requeridos que todo agente de negocio debe conocer:

| # | Campo DB | 日本語 | Validación |
|---|----------|--------|------------|
| 1 | work_content | 業務の内容 | NOT NULL, min 10 chars |
| 2 | responsibility_level | 責任の程度 | NOT NULL |
| 3 | worksite_name | 派遣先事業所名 | NOT NULL |
| 4 | worksite_address | 事業所住所 | NOT NULL |
| 5 | worksite_department | 組織単位 | Optional |
| 6 | supervisor_name | 指揮命令者 | NOT NULL |
| 7 | work_days | 派遣期間 | JSONB array |
| 8 | work_start_time | 始業時刻 | HH:MM format |
| 9 | work_end_time | 終業時刻 | HH:MM format |
| 10 | break_duration | 休憩時間 | Integer (minutes) |
| 11 | safety_hygiene | 安全衛生 | NOT NULL |
| 12 | complaint_handling | 苦情処理 | NOT NULL |
| 13 | contract_termination | 契約解除の措置 | NOT NULL |
| 14 | dispatch_source_manager | 派遣元責任者 | NOT NULL |
| 15 | dispatch_dest_manager | 派遣先責任者 | NOT NULL |
| 16 | overtime_work | 時間外労働 | Integer (hours) |

---

**Fin del Documento**

*Este documento debe ser actualizado cuando se implementen nuevos agentes o cuando cambien los requisitos del negocio.*
