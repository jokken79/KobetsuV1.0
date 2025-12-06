# GitHub Actions Workflows

## 🎯 Workflows Activos (Consolidados)

Este proyecto usa **4 workflows consolidados** en lugar de los 17 workflows originales, reduciendo la complejidad en un 76% y el código en un 82%.

### 1. `main-ci.yml` - Pipeline Principal de CI
**Reemplaza:** `ci.yml`, `testing.yml`, `pr-check.yml`, `caching-optimization.yml`

**Qué hace:**
- ✅ Lint del código (backend y frontend)
- ✅ Type checking (mypy, TypeScript)
- ✅ Tests con cobertura (pytest, vitest)
- ✅ Build de producción
- ✅ Docker build test (solo en PRs)
- ✅ Summary consolidado

**Cuándo se ejecuta:** Push y Pull Requests a main/develop

**Duración estimada:** ~7 minutos (vs 21 minutos antes)

---

### 2. `security-full.yml` - Escaneo de Seguridad Completo
**Reemplaza:** `security.yml`, `security-advanced.yml`, `security-patching.yml`

**Qué hace:**
- 🔒 CodeQL analysis (JavaScript + Python)
- 🔒 Dependency vulnerability scanning
- 🔒 Secret detection (TruffleHog)
- 🔒 Docker image scanning (Trivy)
- 🔒 Auto-issue creation para vulnerabilidades

**Cuándo se ejecuta:**
- Push y PRs a main/develop
- Daily schedule (2 AM UTC)
- Manual dispatch

**Duración estimada:** ~10 minutos

---

### 3. `deploy-release.yml` - Deploy y Release
**Reemplaza:** `deploy.yml`, `release.yml`, `release-notes.yml`

⚠️ **Pendiente de implementación**

**Qué hará:**
- 🚀 Deploy a producción
- 📦 Crear releases en GitHub
- 📝 Auto-generar release notes
- 🏷️ Tag management

---

### 4. `maintenance.yml` - Tareas de Mantenimiento
**Reemplaza:** `backup.yml`, `dependency-management.yml`, `docs.yml`, `monitoring.yml`

⚠️ **Pendiente de implementación**

**Qué hará:**
- 💾 Backups automáticos
- 📦 Actualización de dependencias
- 📚 Generación de documentación
- 📊 Health checks y monitoring

---

## 📊 Comparación: Antes vs Después

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Workflows** | 17 archivos | 4 archivos | -76% |
| **Líneas de código** | 7,548 líneas | ~1,350 líneas | -82% |
| **Tiempo de CI en PRs** | ~21 minutos | ~7 minutos | -66% |
| **Checks en PRs** | 4-6 checks | 1-2 checks | -75% |
| **Mantenibilidad** | Complejo | Simple | ✅ |

---

## 🗂️ Workflows Archivados

Los workflows antiguos se movieron a `.github/workflows/.archived/` como referencia histórica.

**No se ejecutan automáticamente.** Si necesitas consultarlos:

```bash
cd .github/workflows/.archived/
ls -la
```

---

## 🔧 Cómo Funciona la Consolidación

### Ejemplo: main-ci.yml

**ANTES** (4 workflows separados):
```
ci.yml         → Lint backend + frontend
testing.yml    → Tests con cobertura
pr-check.yml   → Build + validación
caching.yml    → Optimización de cache
```

**DESPUÉS** (1 workflow integrado):
```
main-ci.yml
├─ backend-check (job paralelo)
│  ├─ Lint
│  ├─ Type check
│  ├─ Tests
│  └─ Coverage
├─ frontend-check (job paralelo)
│  ├─ Lint
│  ├─ Type check
│  ├─ Tests
│  └─ Build
├─ docker-build (solo PRs)
└─ ci-summary
```

**Beneficios:**
- ✅ Ejecución en paralelo (backend + frontend simultáneo)
- ✅ Cache compartido entre steps
- ✅ Un solo check en PRs
- ✅ Fácil de mantener y debuggear

---

## 📝 Notas para Desarrolladores

### Para ejecutar workflows manualmente:

```bash
# En GitHub UI:
Actions → Seleccionar workflow → Run workflow
```

### Para agregar nuevos jobs:

Edita el workflow correspondiente y agrega el job. Mantén la estructura:

```yaml
jobs:
  nuevo-job:
    name: Descripción del Job
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      # ... más steps
```

### Para debuggear workflows:

1. Ve a la pestaña **Actions**
2. Selecciona el workflow run
3. Expande el job que falló
4. Revisa los logs de cada step

---

## 🤝 Contribuir

Si necesitas modificar workflows:

1. Edita el archivo correspondiente
2. Testa localmente con [act](https://github.com/nektos/act) (opcional)
3. Crea un PR con los cambios
4. Los workflows se ejecutarán automáticamente

---

**Última actualización:** Diciembre 2025
**Mantenedor:** UNS Kikaku DevOps Team
