#!/bin/bash
# =============================================================================
# UNS Kobetsu Keiyakusho - Sistema de Inicialización Completo
# =============================================================================
# Este script configura todo el sistema de principio a fin:
# 1. Levanta los servicios Docker
# 2. Espera a que estén saludables
# 3. Aplica migraciones
# 4. Crea usuario admin (admin@local.dev / admin123)
# 5. Importa factories desde JSON
# 6. Crea datos demo
# 7. Verifica el sistema
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "============================================================"
echo "  UNS Kobetsu Keiyakusho - System Initialization"
echo "============================================================"
echo -e "${NC}"

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not available${NC}"
    exit 1
fi

echo -e "${GREEN}[1/7] Docker available${NC}"

# =============================================================================
# Step 1: Start Docker services
# =============================================================================
echo -e "\n${YELLOW}[2/7] Starting Docker services...${NC}"
docker compose up -d

# =============================================================================
# Step 2: Wait for services to be healthy
# =============================================================================
echo -e "\n${YELLOW}[3/7] Waiting for services to be healthy...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check if backend is healthy
    if docker compose ps | grep -q "uns-kobetsu-backend.*healthy"; then
        echo -e "${GREEN}Backend is healthy!${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for backend to be healthy... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}ERROR: Backend did not become healthy in time${NC}"
    echo "Checking logs..."
    docker compose logs --tail=50 backend
    exit 1
fi

# Show service status
docker compose ps

# =============================================================================
# Step 3: Apply database migrations
# =============================================================================
echo -e "\n${YELLOW}[4/7] Applying database migrations...${NC}"
docker exec uns-kobetsu-backend alembic upgrade head

echo -e "${GREEN}Migrations applied successfully!${NC}"

# =============================================================================
# Step 4: Create admin user
# =============================================================================
echo -e "\n${YELLOW}[5/7] Creating admin user...${NC}"
docker exec uns-kobetsu-backend python scripts/create_admin.py -y \
    --email admin@local.dev \
    --password admin123 \
    --name "Admin User" \
    --role admin

# =============================================================================
# Step 5: Import factories from JSON
# =============================================================================
echo -e "\n${YELLOW}[6/7] Importing factories from JSON...${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if BASEDATEJP/config/factories exists locally
FACTORIES_DIR="${SCRIPT_DIR}/BASEDATEJP/config/factories"
if [ -d "$FACTORIES_DIR" ]; then
    echo "Copying factory JSON files to container..."
    docker cp "$FACTORIES_DIR" uns-kobetsu-backend:/tmp/factories

    # Run import script
    if docker exec uns-kobetsu-backend test -f scripts/import_factories_json.py; then
        docker exec uns-kobetsu-backend python scripts/import_factories_json.py --dir /tmp/factories || true
    else
        echo "Factory JSON import script not found, skipping..."
    fi

    # Cleanup
    docker exec uns-kobetsu-backend rm -rf /tmp/factories
else
    echo "Local factories directory not found at: $FACTORIES_DIR"

    # Try default path in container
    if docker exec uns-kobetsu-backend test -f scripts/import_factories_json.py; then
        docker exec uns-kobetsu-backend python scripts/import_factories_json.py --dir /network_data/config/factories 2>/dev/null || true
    fi
fi

# =============================================================================
# Step 6: Create demo data
# =============================================================================
echo -e "\n${YELLOW}[7/7] Creating demo data...${NC}"
docker exec uns-kobetsu-backend python scripts/import_demo_data.py --count 10 || true

# =============================================================================
# Verification
# =============================================================================
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}  System Verification${NC}"
echo -e "${BLUE}============================================================${NC}"

# Test health endpoint
echo -e "\n${YELLOW}Testing backend health...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:8010/health)
echo "Health: $HEALTH_RESPONSE"

# Test login
echo -e "\n${YELLOW}Testing login...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8010/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@local.dev","password":"admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}Login successful!${NC}"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

    # Test kobetsu stats
    echo -e "\n${YELLOW}Testing kobetsu stats...${NC}"
    STATS_RESPONSE=$(curl -s http://localhost:8010/api/v1/kobetsu/stats \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "Stats: $STATS_RESPONSE"

    # Test factories
    echo -e "\n${YELLOW}Testing factories...${NC}"
    FACTORIES_RESPONSE=$(curl -s "http://localhost:8010/api/v1/factories?limit=5" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "Factories count: $(echo "$FACTORIES_RESPONSE" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "N/A")"
else
    echo -e "${RED}Login failed!${NC}"
    echo "$LOGIN_RESPONSE"
fi

# =============================================================================
# Summary
# =============================================================================
echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}  INITIALIZATION COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "Frontend URL:     ${BLUE}http://localhost:3010${NC}"
echo -e "Backend API:      ${BLUE}http://localhost:8010/api/v1${NC}"
echo -e "API Docs:         ${BLUE}http://localhost:8010/docs${NC}"
echo -e "Adminer (DB UI):  ${BLUE}http://localhost:8090${NC}"
echo ""
echo -e "Login credentials:"
echo -e "  Email:    ${YELLOW}admin@local.dev${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}"
echo ""
echo -e "${GREEN}============================================================${NC}"
