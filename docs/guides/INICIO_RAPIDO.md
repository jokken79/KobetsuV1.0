# 🚀 Inicio Rápido - UNS Kobetsu Keiyakusho

## ✅ Todo está configurado y listo para usar!

### 📋 Configuración Completada

- ✅ **Archivo .env creado** con SECRET_KEY seguro
- ✅ **Docker configurado** con nombres únicos (prefijo `uns-kobetsu-`)
- ✅ **Puertos personalizados** para evitar conflictos:
  - PostgreSQL: **5442**
  - Redis: **6389**
  - Backend: **8010**
  - Frontend: **3010**
  - Adminer: **8090**

---

## 🎯 Cómo Iniciar la Aplicación

### **Paso 1: Iniciar Contenedores**
```bash
docker compose up -d
```

Esto levantará 5 servicios:
- `uns-kobetsu-db` - PostgreSQL Database
- `uns-kobetsu-redis` - Redis Cache
- `uns-kobetsu-backend` - FastAPI Backend
- `uns-kobetsu-frontend` - Next.js Frontend
- `uns-kobetsu-adminer` - Database UI

### **Paso 2: Aplicar Migraciones de Base de Datos**
```bash
docker exec -it uns-kobetsu-backend alembic upgrade head
```

### **Paso 3: Crear Usuario Administrador (Opcional)**
```bash
docker exec -it uns-kobetsu-backend python scripts/create_admin.py
```

### **Paso 4: Acceder a la Aplicación**
```
🌐 Frontend:  http://localhost:3010
📚 API Docs:  http://localhost:8010/docs
🗄️  Adminer:  http://localhost:8090
```

---

## 📝 Credenciales de Base de Datos

Para acceder a Adminer (http://localhost:8090):

```
Sistema:     PostgreSQL
Servidor:    uns-kobetsu-db
Usuario:     kobetsu_admin
Contraseña:  KobetsuSecure2024!Pass
Base datos:  kobetsu_db
```

---

## 🔄 Comandos Útiles

### Ver Estado de Contenedores
```bash
docker compose ps
```

### Ver Logs
```bash
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f uns-kobetsu-backend

# Solo frontend
docker compose logs -f uns-kobetsu-frontend
```

### Detener Servicios
```bash
docker compose down
```

### Detener y Eliminar Volúmenes (⚠️ Borra todos los datos)
```bash
docker compose down -v
```

### Reiniciar un Servicio
```bash
docker compose restart uns-kobetsu-backend
```

### Reconstruir Imágenes
```bash
docker compose build --no-cache
docker compose up -d
```

---

## 📊 Importar Datos Demo

### Opción 1: Desde el Contenedor
```bash
# Si tienes un script de datos demo
docker exec -it uns-kobetsu-backend python scripts/import_demo_data.py
```

### Opción 2: Desde la UI
1. Ve a http://localhost:3010/import
2. Arrastra tu archivo Excel/JSON
3. Preview de datos
4. Click en "Importar"

---

## 🛠️ Solución de Problemas

### Problema: "Puerto ya en uso"
Si algún puerto está ocupado, edita `.env`:
```bash
KOBETSU_DB_PORT=5443       # Cambiar 5442 → 5443
KOBETSU_BACKEND_PORT=8011  # Cambiar 8010 → 8011
# etc...
```

### Problema: "Database not found"
```bash
docker exec -it uns-kobetsu-backend alembic upgrade head
```

### Problema: "Cannot connect to backend"
```bash
# Ver logs
docker compose logs uns-kobetsu-backend

# Reiniciar
docker compose restart uns-kobetsu-backend
```

### Problema: Volúmenes de Docker antiguos
```bash
# Listar volúmenes
docker volume ls | grep kobetsu

# Eliminar volúmenes antiguos (si existen)
docker volume rm kobetsu-keiyakusho-postgres-data
docker volume rm kobetsu-keiyakusho-redis-data
```

---

## 🎨 Uso Básico

### 1. Crear un Contrato
1. Ve a http://localhost:3010/kobetsu/create
2. Selecciona la 派遣先 (Factory)
3. Selecciona empleados
4. Completa los detalles
5. Click "Guardar"

### 2. Ver Dashboard
1. Ve a http://localhost:3010/kobetsu
2. Verás estadísticas y lista de contratos
3. Usa filtros para buscar

### 3. Generar Documentos
1. Abre un contrato
2. Click en "Generar Documentos"
3. Selecciona tipo (個別契約書, 就業条件明示書, etc.)
4. Descarga el PDF/DOCX

---

## 📁 Estructura de Nombres en Docker

Todos los recursos de esta app usan el prefijo `uns-kobetsu-`:

**Contenedores:**
- `uns-kobetsu-db`
- `uns-kobetsu-redis`
- `uns-kobetsu-backend`
- `uns-kobetsu-frontend`
- `uns-kobetsu-adminer`

**Volúmenes:**
- `uns-kobetsu-keiyakusho-postgres-data`
- `uns-kobetsu-keiyakusho-redis-data`
- `uns-kobetsu-keiyakusho-outputs`

**Imágenes:**
- `uns-kobetsu-keiyakusho-backend:latest`
- `uns-kobetsu-keiyakusho-frontend:latest`

**Red:**
- `uns-kobetsu-keiyakusho-network`

Esto evita conflictos con otras aplicaciones Docker.

---

## 🔐 Seguridad

Como esta app es para **uso personal**, la configuración actual es suficiente:

- ✅ SECRET_KEY generado aleatoriamente
- ✅ Contraseña de DB cambiada del default
- ✅ Puertos únicos configurados
- ✅ Red Docker aislada

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs: `docker compose logs -f`
2. Verifica que todos los servicios estén healthy: `docker compose ps`
3. Reinicia los servicios: `docker compose restart`

---

**¡Listo para usar! 🎉**

Desarrollado para UNS Kikaku
