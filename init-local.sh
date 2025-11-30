#!/bin/bash

#############################################################################
# Local Development Initialization Script for UNS-Kobetsu System
#
# Usage:
#   ./init-local.sh                  # Standard initialization
#   ./init-local.sh --reset          # Reset everything (CAUTION: Data loss!)
#   ./init-local.sh --logs           # Start with log following
#   ./init-local.sh --quick          # Skip health checks for faster startup
#   ./init-local.sh --import-demo    # Import demo data after startup
#
# Features:
#   - Checks prerequisites (Docker, Docker Compose)
#   - Creates necessary directories
#   - Sets up environment variables
#   - Starts all services
#   - Runs database migrations
#   - Performs health checks
#   - Optional demo data import
#############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
RESET_MODE=false
FOLLOW_LOGS=false
QUICK_MODE=false
IMPORT_DEMO=false
PROJECT_NAME="uns-kobetsu"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET_MODE=true
            shift
            ;;
        --logs)
            FOLLOW_LOGS=true
            shift
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --import-demo)
            IMPORT_DEMO=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --reset        Reset everything (removes volumes, data)"
            echo "  --logs         Follow logs after startup"
            echo "  --quick        Skip health checks for faster startup"
            echo "  --import-demo  Import demo data after startup"
            echo "  --help         Show this help message"
            echo ""
            echo "This script initializes the UNS-Kobetsu development environment."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to check command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=0

    echo -n "  Waiting for $service (port $port)..."
    while [ $attempt -lt $max_attempts ]; do
        if nc -z localhost "$port" 2>/dev/null; then
            echo -e " ${GREEN}ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo -e " ${RED}timeout${NC}"
    return 1
}

# Main banner
clear
echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     UNS KOBETSU KEIYAKUSHO - Local Development Setup        ║"
echo "║     個別契約書管理システム                                    ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Reset mode warning
if [ "$RESET_MODE" = true ]; then
    echo -e "${YELLOW}⚠️  RESET MODE ACTIVATED ⚠️${NC}"
    echo "This will:"
    echo "  • Stop all containers"
    echo "  • Remove all volumes (DATABASE WILL BE DELETED)"
    echo "  • Remove all generated files"
    echo ""
    read -p "Are you absolutely sure? Type 'yes' to continue: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Reset cancelled."
        exit 0
    fi
fi

# Check prerequisites
print_header "Checking Prerequisites"

PREREQ_FAILED=false
check_command "docker" || PREREQ_FAILED=true
check_command "docker compose" || check_command "docker-compose" || PREREQ_FAILED=true
check_command "nc" || echo -e "${YELLOW}⚠ netcat not found (health checks will be skipped)${NC}"

if [ "$PREREQ_FAILED" = true ]; then
    echo ""
    echo -e "${RED}Prerequisites not met. Please install missing tools.${NC}"
    exit 1
fi

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker and try again."
    exit 1
else
    echo -e "${GREEN}✓${NC} Docker daemon is running"
fi

# Reset if requested
if [ "$RESET_MODE" = true ]; then
    print_header "Performing Reset"

    echo "Stopping containers..."
    docker compose down -v 2>/dev/null || true

    echo "Removing volumes..."
    docker volume rm ${PROJECT_NAME}_postgres_data 2>/dev/null || true
    docker volume rm ${PROJECT_NAME}_redis_data 2>/dev/null || true

    echo "Cleaning directories..."
    rm -rf ./backend/logs/* 2>/dev/null || true
    rm -rf ./backend/uploads/* 2>/dev/null || true
    rm -rf ./backend/output/* 2>/dev/null || true
    rm -rf ./frontend/.next 2>/dev/null || true
    rm -rf ./backups/* 2>/dev/null || true

    echo -e "${GREEN}✓ Reset complete${NC}"
fi

# Setup environment
print_header "Setting Up Environment"

# Check for .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✓${NC} .env file created"
        echo -e "${YELLOW}⚠ Please review .env and update settings if needed${NC}"
    else
        echo -e "${RED}✗ No .env or .env.example file found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p ./backend/logs
mkdir -p ./backend/uploads
mkdir -p ./backend/output/pdf
mkdir -p ./backups
mkdir -p ./frontend/.next
echo -e "${GREEN}✓${NC} Directories created"

# Make scripts executable
echo "Setting script permissions..."
chmod +x ./scripts/*.sh 2>/dev/null || true
echo -e "${GREEN}✓${NC} Scripts are executable"

# Start services
print_header "Starting Services"

echo "Building and starting containers..."
if docker compose up -d --build; then
    echo -e "${GREEN}✓${NC} Containers started"
else
    echo -e "${RED}✗ Failed to start containers${NC}"
    echo "Check docker-compose.yml and try again"
    exit 1
fi

# Show container status
echo ""
echo "Container status:"
docker compose ps

# Wait for services to be ready
if [ "$QUICK_MODE" = false ]; then
    print_header "Waiting for Services"

    wait_for_service "PostgreSQL" 5442
    wait_for_service "Redis" 6389
    wait_for_service "Backend" 8010
    wait_for_service "Frontend" 3010

    # Additional wait for backend to fully initialize
    echo "  Waiting for backend initialization..."
    sleep 5
fi

# Run database migrations
print_header "Database Setup"

echo "Running database migrations..."
if docker exec ${PROJECT_NAME}-backend alembic upgrade head; then
    echo -e "${GREEN}✓${NC} Migrations completed"
else
    echo -e "${YELLOW}⚠ Migration failed or already up-to-date${NC}"
fi

# Verify setup
if [ "$QUICK_MODE" = false ]; then
    print_header "Verifying Setup"

    echo "Running backend verification..."
    docker exec ${PROJECT_NAME}-backend python scripts/verify_setup.py || true
fi

# Import demo data if requested
if [ "$IMPORT_DEMO" = true ]; then
    print_header "Importing Demo Data"

    echo "Creating admin user..."
    docker exec ${PROJECT_NAME}-backend python scripts/create_admin.py || echo "Admin may already exist"

    echo "Importing demo contracts..."
    docker exec ${PROJECT_NAME}-backend python scripts/import_demo_data.py || echo "Demo data import failed"
fi

# Health check
if [ "$QUICK_MODE" = false ]; then
    print_header "Health Check"

    echo "Checking API health..."
    if curl -s http://localhost:8010/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC} API is healthy"
    else
        echo -e "${YELLOW}⚠ API health check failed${NC}"
    fi

    echo "Checking detailed health..."
    curl -s http://localhost:8010/api/v1/health/detailed | python3 -m json.tool 2>/dev/null || echo "Detailed health not available"
fi

# Summary
print_header "Setup Complete!"

echo -e "${GREEN}The UNS-Kobetsu system is ready!${NC}"
echo ""
echo "Access points:"
echo "  • Frontend:    ${BLUE}http://localhost:3010${NC}"
echo "  • API Docs:    ${BLUE}http://localhost:8010/docs${NC}"
echo "  • Adminer:     ${BLUE}http://localhost:8090${NC}"
echo ""
echo "Default credentials:"
echo "  • Username: admin@uns-kobetsu.com"
echo "  • Password: admin123"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker compose logs -f"
echo "  • Stop services:    docker compose down"
echo "  • Backup database:  ./scripts/backup.sh"
echo "  • Run tests:        docker exec ${PROJECT_NAME}-backend pytest"
echo "  • Clean system:     ./scripts/cleanup.sh"
echo ""
echo "Documentation:"
echo "  • API Docs:  http://localhost:8010/docs"
echo "  • Project:   See README.md and CLAUDE.md"

# Follow logs if requested
if [ "$FOLLOW_LOGS" = true ]; then
    echo ""
    echo -e "${YELLOW}Following logs (Ctrl+C to stop)...${NC}"
    docker compose logs -f
fi