#!/bin/bash

# ========================================
# UNS Kobetsu Keiyakusho - Endpoint Verification Script
# ========================================
# Este script verifica que todos los endpoints respondan correctamente
# después de levantar los servicios con docker-compose

set -e

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# URLs base
BACKEND_URL="http://localhost:8010"
FRONTEND_URL="http://localhost:3010"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}UNS Kobetsu Keiyakusho - Endpoint Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Función para verificar endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}

    echo -n "Verificando $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL (HTTP $response, esperado $expected_code)${NC}"
        return 1
    fi
}

# Contador de errores
errors=0

echo -e "${YELLOW}[1/3] Verificando servicios de infraestructura...${NC}"
echo ""

# PostgreSQL (a través de Adminer)
if ! check_endpoint "http://localhost:8090" "Adminer (PostgreSQL UI)"; then
    ((errors++))
fi

echo ""
echo -e "${YELLOW}[2/3] Verificando Backend (FastAPI)...${NC}"
echo ""

# Backend endpoints
if ! check_endpoint "$BACKEND_URL/" "Backend root"; then
    ((errors++))
fi

if ! check_endpoint "$BACKEND_URL/health" "Health check"; then
    ((errors++))
fi

if ! check_endpoint "$BACKEND_URL/ready" "Readiness check"; then
    ((errors++))
fi

if ! check_endpoint "$BACKEND_URL/docs" "API Documentation (Swagger)"; then
    ((errors++))
fi

if ! check_endpoint "$BACKEND_URL/redoc" "API Documentation (ReDoc)"; then
    ((errors++))
fi

echo ""
echo -e "${YELLOW}[3/3] Verificando Frontend (Next.js)...${NC}"
echo ""

# Frontend endpoints
if ! check_endpoint "$FRONTEND_URL" "Frontend homepage"; then
    ((errors++))
fi

# Resumen final
echo ""
echo -e "${BLUE}========================================${NC}"
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ Todos los endpoints responden correctamente!${NC}"
    echo -e "${GREEN}   La aplicación está funcionando correctamente.${NC}"
    exit 0
else
    echo -e "${RED}❌ $errors endpoint(s) fallaron.${NC}"
    echo -e "${RED}   Por favor revisa los logs de Docker:${NC}"
    echo -e "${YELLOW}   docker-compose logs backend${NC}"
    echo -e "${YELLOW}   docker-compose logs frontend${NC}"
    exit 1
fi
