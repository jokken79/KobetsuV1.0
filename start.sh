#!/bin/bash

# ========================================
# UNS Kobetsu Keiyakusho - Script de Inicio
# ========================================

echo "🚀 Iniciando UNS Kobetsu Keiyakusho..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que Docker esté corriendo
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker no está corriendo${NC}"
    echo "Por favor inicia Docker Desktop y vuelve a intentar"
    exit 1
fi

echo -e "${GREEN}✅ Docker está corriendo${NC}"

# Verificar que existe .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: Archivo .env no encontrado${NC}"
    echo "Creando .env desde .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ Archivo .env creado${NC}"
fi

# Iniciar servicios
echo ""
echo -e "${YELLOW}📦 Iniciando contenedores Docker...${NC}"
docker compose up -d

# Esperar a que los servicios estén listos
echo ""
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
sleep 10

# Verificar estado de contenedores
echo ""
echo -e "${YELLOW}🔍 Verificando estado de contenedores...${NC}"
docker compose ps

# Aplicar migraciones
echo ""
echo -e "${YELLOW}🗄️  Aplicando migraciones de base de datos...${NC}"
docker exec -it uns-kobetsu-backend alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migraciones aplicadas correctamente${NC}"
else
    echo -e "${RED}⚠️  Error al aplicar migraciones${NC}"
fi

# Mostrar URLs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ UNS Kobetsu Keiyakusho está corriendo!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "🌐 Frontend:   ${YELLOW}http://localhost:3010${NC}"
echo -e "📚 API Docs:   ${YELLOW}http://localhost:8010/docs${NC}"
echo -e "🗄️  Adminer:    ${YELLOW}http://localhost:8090${NC}"
echo ""
echo -e "${GREEN}Credenciales de Adminer:${NC}"
echo "  Sistema:     PostgreSQL"
echo "  Servidor:    uns-kobetsu-db"
echo "  Usuario:     kobetsu_admin"
echo "  Contraseña:  KobetsuSecure2024!Pass"
echo "  Base datos:  kobetsu_db"
echo ""
echo -e "${YELLOW}📝 Comandos útiles:${NC}"
echo "  Ver logs:        docker compose logs -f"
echo "  Detener:         docker compose down"
echo "  Reiniciar:       docker compose restart"
echo ""
echo -e "${GREEN}¡Listo para usar! 🎉${NC}"
