#!/bin/bash
# ============================================
# Mostrar todas las apps Docker del usuario
# ============================================
# Agrupa contenedores por app usando labels
# ============================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

clear
echo ""
echo -e "${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║           🐳 MIS APLICACIONES DOCKER                       ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo${NC}"
    exit 1
fi

# Obtener todas las apps únicas por label
echo -e "${CYAN}📦 APLICACIONES DETECTADAS${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Obtener labels de app.name únicos
APPS=$(docker ps -a --format "{{.Label \"app.name\"}}" 2>/dev/null | sort -u | grep -v "^$")

# Si no hay apps con labels, mostrar por prefijo de nombre
if [ -z "$APPS" ]; then
    echo -e "${YELLOW}No se encontraron apps con labels.${NC}"
    echo -e "${YELLOW}Mostrando por prefijo de nombre de contenedor...${NC}"
    echo ""

    # Agrupar por prefijo (antes del primer -)
    docker ps -a --format "{{.Names}}" | cut -d'-' -f1-2 | sort -u | while read prefix; do
        echo -e "${GREEN}📁 $prefix${NC}"
        docker ps -a --filter "name=$prefix" --format "   └─ {{.Names}}: {{.Status}} ({{.Ports}})" | head -10
        echo ""
    done
else
    # Mostrar por app.name label
    for app in $APPS; do
        # Contar contenedores de esta app
        COUNT=$(docker ps -a --filter "label=app.name=$app" --format "{{.Names}}" | wc -l)
        RUNNING=$(docker ps --filter "label=app.name=$app" --format "{{.Names}}" | wc -l)

        # Color según estado
        if [ "$RUNNING" -eq "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
            STATUS_COLOR="${GREEN}"
            STATUS_ICON="🟢"
        elif [ "$RUNNING" -gt 0 ]; then
            STATUS_COLOR="${YELLOW}"
            STATUS_ICON="🟡"
        else
            STATUS_COLOR="${RED}"
            STATUS_ICON="🔴"
        fi

        echo -e "${BOLD}${STATUS_ICON} ${STATUS_COLOR}$app${NC} ($RUNNING/$COUNT contenedores)"
        echo "   ────────────────────────────────────────"

        # Mostrar contenedores de esta app
        docker ps -a --filter "label=app.name=$app" --format "{{.Names}}|{{.Status}}|{{.Ports}}" | while IFS='|' read name status ports; do
            # Determinar icono de estado
            if [[ "$status" == *"Up"* ]]; then
                icon="✅"
            else
                icon="⬚ "
            fi

            # Limpiar puertos
            clean_ports=$(echo "$ports" | sed 's/0.0.0.0://g' | sed 's/->.*//g' | tr ',' ' ')

            if [ -n "$clean_ports" ]; then
                echo -e "   $icon $name ${CYAN}:$clean_ports${NC}"
            else
                echo "   $icon $name"
            fi
        done
        echo ""
    done
fi

# ============================================
# Tabla resumen de puertos
# ============================================
echo -e "${CYAN}🔌 TABLA DE PUERTOS EN USO${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""
printf "${BOLD}%-25s %-10s %-35s${NC}\n" "APLICACIÓN" "PUERTO" "URL"
echo "────────────────────────────────────────────────────────────────────"

docker ps --format "{{.Label \"app.name\"}}|{{.Ports}}|{{.Label \"app.component\"}}" 2>/dev/null | \
    grep -v "^|" | sort -u | while IFS='|' read app ports component; do

    # Extraer puerto host
    port=$(echo "$ports" | grep -oE '0\.0\.0\.0:[0-9]+' | head -1 | cut -d: -f2)

    if [ -n "$port" ] && [ -n "$app" ]; then
        # Determinar URL basado en componente
        case "$component" in
            "frontend")
                url="http://localhost:$port"
                ;;
            "backend")
                url="http://localhost:$port/docs"
                ;;
            "adminer"|"database-ui")
                url="http://localhost:$port"
                ;;
            *)
                url="localhost:$port"
                ;;
        esac

        printf "%-25s %-10s %-35s\n" "$app" "$port" "$url"
    fi
done

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================
# Comandos útiles
# ============================================
echo -e "${CYAN}📝 COMANDOS ÚTILES${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Ver puertos detallados:     ./scripts/docker-ports.sh"
echo "  Iniciar UNS-Kobetsu:        docker compose up -d"
echo "  Detener UNS-Kobetsu:        docker compose down"
echo "  Ver logs:                   docker compose logs -f"
echo "  Estado de contenedores:     docker compose ps"
echo ""
