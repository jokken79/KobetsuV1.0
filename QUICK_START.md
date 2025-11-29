# 🚀 Guía de Instalación Rápida

Esta guía te ayudará a poner en marcha el sistema de 個別契約書 en menos de 10 minutos.

## 📋 **Pre-requisitos**

Asegúrate de tener instalado:

- ✅ **Docker Desktop** (Windows/Mac) o **Docker Engine** (Linux)
  - [Descargar Docker Desktop](https://www.docker.com/products/docker-desktop)
- ✅ **Git**
  - [Descargar Git](https://git-scm.com/downloads)
- ✅ **4GB RAM disponible**
- ✅ **10GB espacio en disco**

## ⚡ **Instalación Express (5 minutos)**

### **Paso 1: Clonar el Repositorio**

```bash
git clone https://github.com/jokken79/UNS-Kobetsu-Keiyakusho.git
cd UNS-Kobetsu-Keiyakusho
```

### **Paso 2: Configurar Variables de Entorno**

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Opcional: Editar .env con tus valores
# Por defecto ya funciona, pero en producción DEBES cambiar las contraseñas
nano .env  # o usa tu editor favorito
```

**⚠️ IMPORTANTE en Producción:**
```bash
# Generar SECRET_KEY seguro
openssl rand -hex 32

# Cambiar en .env:
SECRET_KEY=<tu-key-generado>
POSTGRES_PASSWORD=<password-fuerte>
```

### **Paso 3: Iniciar Servicios**

```bash
# Iniciar todos los servicios con Docker Compose
docker compose up -d

# Ver el progreso
docker compose logs -f
```

**Espera 1-2 minutos** mientras se construyen las imágenes y se inician los servicios.

### **Paso 4: Aplicar Migraciones de Base de Datos**

```bash
# Aplicar todas las migraciones
docker exec -it kobetsu-backend alembic upgrade head
```

### **Paso 5: Crear Usuario Administrador**

```bash
# Crear usuario admin
docker exec -it kobetsu-backend python scripts/create_admin.py

# Credenciales por defecto:
# Usuario: admin
# Password: admin123
```

### **Paso 6: (Opcional) Importar Datos de Demostración**

```bash
# Importar factories y employees de ejemplo
docker exec -it kobetsu-backend python scripts/import_demo_data.py
```

## ✅ **Verificar Instalación**

### **1. Verificar que todos los servicios estén corriendo**

```bash
docker compose ps
```

Deberías ver:
```
NAME                STATUS              PORTS
kobetsu-backend     Up (healthy)        0.0.0.0:8000->8000/tcp
kobetsu-frontend    Up (healthy)        0.0.0.0:3000->3000/tcp
kobetsu-db          Up (healthy)        0.0.0.0:5432->5432/tcp
kobetsu-redis       Up (healthy)        0.0.0.0:6379->6379/tcp
kobetsu-adminer     Up                  0.0.0.0:8080->8080/tcp
```

### **2. Acceder a los Servicios**

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3000 | Interfaz principal |
| **API Docs** | http://localhost:8000/api/docs | Documentación Swagger |
| **Adminer** | http://localhost:8080 | Gestor de base de datos |

### **3. Hacer Login**

1. Ir a: http://localhost:3000
2. Login con:
   - **Usuario:** `admin`
   - **Password:** `admin123`

## 📊 **Crear tu Primer 個別契約書**

### **Opción A: Desde la Interfaz Web**

1. **Login** en http://localhost:3000
2. **Menú → 個別契約書 → 新規作成**
3. **Completar el formulario:**
   - Seleccionar 派遣先 (Empresa Cliente)
   - Seleccionar Trabajadores
   - Fechas de dispatch
   - Condiciones laborales
4. **Generar Contrato** → Se creará automáticamente el PDF

### **Opción B: Desde la API**

```bash
# Primero obtener el token JWT
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Crear el contrato
curl -X POST http://localhost:8000/api/kobetsu \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "factory_id": 1,
  "employee_ids": [1, 2],
  "contract_date": "2024-11-25",
  "dispatch_start_date": "2024-12-01",
  "dispatch_end_date": "2025-11-30",
  "work_content": "製造ライン作業、検品業務",
  "responsibility_level": "通常業務",
  "worksite_name": "トヨタ自動車株式会社",
  "worksite_address": "愛知県豊田市トヨタ町1番地",
  "supervisor_department": "製造部",
  "supervisor_position": "課長",
  "supervisor_name": "山田太郎",
  "work_days": ["月", "火", "水", "木", "金"],
  "work_start_time": "08:00",
  "work_end_time": "17:00",
  "break_time_minutes": 60,
  "hourly_rate": 1500,
  "overtime_rate": 1875,
  "haken_moto_complaint_contact": {
    "department": "総務部",
    "position": "部長",
    "name": "金城賢士",
    "phone": "0568-00-0000"
  },
  "haken_saki_complaint_contact": {
    "department": "人事部",
    "position": "課長",
    "name": "山田太郎",
    "phone": "0565-12-3456"
  },
  "haken_moto_manager": {
    "department": "派遣事業部",
    "position": "責任者",
    "name": "金城賢士",
    "phone": "0568-00-0000"
  },
  "haken_saki_manager": {
    "department": "製造部",
    "position": "責任者",
    "name": "田中一郎",
    "phone": "0565-12-3456"
  }
}
EOF
```

## 🛠️ **Comandos Útiles**

```bash
# Ver logs en tiempo real
docker compose logs -f

# Ver logs solo del backend
docker compose logs -f backend

# Reiniciar un servicio
docker compose restart backend

# Detener todos los servicios
docker compose down

# Detener y eliminar datos (⚠️ CUIDADO: Borra la base de datos)
docker compose down -v

# Reconstruir servicios
docker compose up -d --build

# Acceder al contenedor del backend
docker exec -it kobetsu-backend bash

# Acceder a la base de datos
docker exec -it kobetsu-db psql -U kobetsu_admin -d kobetsu_db
```

## 🔧 **Solución de Problemas**

### **Error: Puerto ya en uso**

```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

### **Error: Backend no conecta a DB**

```bash
# Verificar que DB esté corriendo
docker compose ps db

# Ver logs de DB
docker compose logs db

# Reiniciar DB
docker compose restart db

# Esperar 10 segundos y reiniciar backend
docker compose restart backend
```

### **Error: "alembic: command not found"**

```bash
# Instalar alembic en el contenedor
docker exec -it kobetsu-backend pip install alembic
docker compose restart backend
```

### **Frontend no carga**

```bash
# Limpiar cache de Next.js
docker exec -it kobetsu-frontend rm -rf .next

# Reinstalar dependencias
docker exec -it kobetsu-frontend npm install

# Reconstruir
docker compose up -d --build frontend
```

## 📚 **Próximos Pasos**

1. ✅ **[Ver Documentación API](docs/API.md)**
2. ✅ **[Leer Requisitos Legales](docs/LEGAL.md)**
3. ✅ **[Guía de Integración con UNS-ClaudeJP](docs/INTEGRATION.md)**
4. ✅ **[Personalizar Templates](docs/TEMPLATES.md)**

## 💡 **Tips**

- 🔐 **Cambiar contraseñas en producción**
- 📧 **Configurar notificaciones por email**
- 🔄 **Hacer backups regulares de la base de datos**
- 📊 **Revisar el dashboard diariamente**
- 🎨 **Personalizar la plantilla de PDF según tu empresa**

## 🆘 **¿Necesitas Ayuda?**

- 📖 [Documentación Completa](https://github.com/jokken79/UNS-Kobetsu-Keiyakusho/wiki)
- 🐛 [Reportar un Bug](https://github.com/jokken79/UNS-Kobetsu-Keiyakusho/issues)
- 💬 [Discusiones](https://github.com/jokken79/UNS-Kobetsu-Keiyakusho/discussions)

---

**¡Felicidades!** 🎉 Ya tienes el sistema de 個別契約書 funcionando.

[⬅ Volver al README](README.md)
