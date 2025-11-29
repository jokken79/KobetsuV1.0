#!/bin/bash
# ============================================
# Docker Ports Manager
# ============================================
# Muestra todos los puertos usados por contenedores Docker
# y ayuda a identificar qué app usa cada puerto
# ============================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}   🐳 DOCKER PORTS MANAGER${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

# Verificar que Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    exit 1
fi

# ============================================
# Mostrar puertos de UNS-Kobetsu
# ============================================
echo -e "${CYAN}📦 UNS-KOBETSU-KEIYAKUSHO${NC}"
echo -e "${CYAN}----------------------------------------${NC}"

# Verificar si los contenedores de UNS-Kobetsu están corriendo
KOBETSU_CONTAINERS=$(docker ps --filter "label=app.name=uns-kobetsu-keiyakusho" --format "{{.Names}}" 2>/dev/null)

if [ -z "$KOBETSU_CONTAINERS" ]; then
    echo -e "${YELLOW}⚠️  Contenedores no están corriendo${NC}"
    echo ""
    echo "   Puertos configurados (cuando se inicie):"
    echo -e "   ${GREEN}Frontend:${NC}  http://localhost:${KOBETSU_FRONTEND_PORT:-3010}"
    echo -e "   ${GREEN}Backend:${NC}   http://localhost:${KOBETSU_BACKEND_PORT:-8010}"
    echo -e "   ${GREEN}API Docs:${NC}  http://localhost:${KOBETSU_BACKEND_PORT:-8010}/docs"
    echo -e "   ${GREEN}Adminer:${NC}   http://localhost:${KOBETSU_ADMINER_PORT:-8090}"
    echo -e "   ${GREEN}Postgres:${NC}  localhost:${KOBETSU_DB_PORT:-5442}"
    echo -e "   ${GREEN}Redis:${NC}     localhost:${KOBETSU_REDIS_PORT:-6389}"
else
    docker ps --filter "label=app.name=uns-kobetsu-keiyakusho" \
        --format "   {{.Names}}: {{.Ports}}" | \
        sed 's/0.0.0.0://g' | \
        sed 's/->/ → /g'
fi
echo ""

# ============================================
# Mostrar TODOS los contenedores con puertos
# ============================================
echo -e "${CYAN}🌐 TODOS LOS CONTENEDORES CON PUERTOS${NC}"
echo -e "${CYAN}----------------------------------------${NC}"

# Obtener todos los contenedores con puertos
ALL_CONTAINERS=$(docker ps --format "{{.Names}}|{{.Ports}}|{{.Image}}" 2>/dev/null | grep -v "^$")

if [ -z "$ALL_CONTAINERS" ]; then
    echo -e "${YELLOW}⚠️  No hay contenedores corriendo${NC}"
else
    printf "   ${BOLD}%-30s %-25s %s${NC}\n" "CONTENEDOR" "PUERTO(S)" "IMAGEN"
    echo "   ────────────────────────────────────────────────────────────────────────"

    echo "$ALL_CONTAINERS" | while IFS='|' read -r name ports image; do
        # Limpiar puertos
        clean_ports=$(echo "$ports" | sed 's/0.0.0.0://g' | sed 's/->.*,/,/g' | sed 's/->.*//' | tr ',' ' ')

        if [ -n "$clean_ports" ]; then
            printf "   %-30s %-25s %s\n" "$name" "$clean_ports" "$image"
        fi
    done
fi
echo ""

# ============================================
# Mostrar puertos en uso en el sistema
# ============================================
echo -e "${CYAN}🔌 PUERTOS EN USO (Sistema)${NC}"
echo -e "${CYAN}----------------------------------------${NC}"

# Lista de puertos comunes para verificar
COMMON_PORTS="80 443 3000 3010 5432 5442 6379 6389 8000 8010 8080 8090 9000"

echo -e "   ${BOLD}Puerto    Estado    Usado por${NC}"
echo "   ────────────────────────────────────"

for port in $COMMON_PORTS; do
    if lsof -i :$port > /dev/null 2>&1; then
        PROCESS=$(lsof -i :$port -t 2>/dev/null | head -1)
        PROCESS_NAME=$(ps -p $PROCESS -o comm= 2>/dev/null || echo "unknown")
        echo -e "   ${RED}$port${NC}      EN USO    $PROCESS_NAME"
    else
        echo -e "   ${GREEN}$port${NC}      libre     -"
    fi
done
echo ""

# ============================================
# Resumen de puertos de UNS-Kobetsu
# ============================================
echo -e "${CYAN}📋 CONFIGURACIÓN DE PUERTOS UNS-KOBETSU${NC}"
echo -e "${CYAN}----------------------------------------${NC}"
echo ""
echo "   Para cambiar puertos, edita el archivo .env:"
echo ""
echo -e "   ${BOLD}# Archivo: .env${NC}"
echo "   KOBETSU_FRONTEND_PORT=3010    # Frontend Next.js"
echo "   KOBETSU_BACKEND_PORT=8010     # Backend FastAPI"
echo "   KOBETSU_ADMINER_PORT=8090     # Adminer DB UI"
echo "   KOBETSU_DB_PORT=5442          # PostgreSQL"
echo "   KOBETSU_REDIS_PORT=6389       # Redis Cache"
echo ""
echo -e "${CYAN}----------------------------------------${NC}"
echo ""

# ============================================
# Sugerir puertos libres si hay conflictos
# ============================================
check_port_conflict() {
    local port=$1
    local name=$2
    if lsof -i :$port > /dev/null 2>&1; then
        # Buscar puerto libre cercano
        local new_port=$((port + 1))
        while lsof -i :$new_port > /dev/null 2>&1; do
            new_port=$((new_port + 1))
        done
        echo -e "${YELLOW}⚠️  Puerto $port ($name) en uso. Sugerencia: usar $new_port${NC}"
    fi
}

echo -e "${CYAN}🔍 VERIFICACIÓN DE CONFLICTOS${NC}"
echo -e "${CYAN}----------------------------------------${NC}"

CONFLICTS=0
check_port_conflict ${KOBETSU_FRONTEND_PORT:-3010} "Frontend" && CONFLICTS=1
check_port_conflict ${KOBETSU_BACKEND_PORT:-8010} "Backend" && CONFLICTS=1
check_port_conflict ${KOBETSU_ADMINER_PORT:-8090} "Adminer" && CONFLICTS=1
check_port_conflict ${KOBETSU_DB_PORT:-5442} "PostgreSQL" && CONFLICTS=1
check_port_conflict ${KOBETSU_REDIS_PORT:-6389} "Redis" && CONFLICTS=1

if [ "$CONFLICTS" -eq 0 ]; then
    echo -e "${GREEN}✅ No hay conflictos de puertos${NC}"
fi

echo ""
echo -e "${BOLD}============================================${NC}"
