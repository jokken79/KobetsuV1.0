#!/bin/bash

#############################################################################
# Database Restore Script for UNS-Kobetsu System
#
# Usage:
#   ./scripts/restore.sh backup_file.sql.gz  # Restore specific backup
#   ./scripts/restore.sh --list              # List available backups
#   ./scripts/restore.sh --latest            # Restore latest backup
#
# Features:
#   - Restores from gzip compressed backups
#   - Creates safety backup before restore
#   - Verifies backup integrity before restore
#   - Shows backup metadata before confirmation
#############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_CONTAINER="uns-kobetsu-db"
DB_NAME="${POSTGRES_DB:-kobetsu_db}"
DB_USER="${POSTGRES_USER:-kobetsu_admin}"

# Function to list available backups
list_backups() {
    echo -e "${BLUE}=== Available Backups ===${NC}"
    if [ -d "$BACKUP_DIR" ] && [ -n "$(ls -A "$BACKUP_DIR"/kobetsu_backup_*.sql.gz 2>/dev/null)" ]; then
        ls -lh "$BACKUP_DIR"/kobetsu_backup_*.sql.gz | while read -r line; do
            FILE=$(echo "$line" | awk '{print $9}')
            META="${FILE%.sql.gz}.meta"
            if [ -f "$META" ]; then
                echo ""
                echo "File: $(basename "$FILE")"
                echo "Size: $(echo "$line" | awk '{print $5}')"
                cat "$META" | grep -E "Timestamp|Size|Contracts|Employees" | sed 's/^/  /'
            else
                echo "$line"
            fi
        done
    else
        echo "No backups found in $BACKUP_DIR"
    fi
}

# Function to get latest backup file
get_latest_backup() {
    LATEST=$(ls -t "$BACKUP_DIR"/kobetsu_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
        echo -e "${RED}No backup files found in $BACKUP_DIR${NC}"
        exit 1
    fi
    echo "$LATEST"
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file> | --list | --latest"
    echo ""
    echo "Options:"
    echo "  backup_file    Path to backup file to restore"
    echo "  --list         List available backups"
    echo "  --latest       Restore the most recent backup"
    echo "  --help         Show this help message"
    exit 1
fi

case $1 in
    --list)
        list_backups
        exit 0
        ;;
    --latest)
        BACKUP_FILE=$(get_latest_backup)
        echo "Using latest backup: $BACKUP_FILE"
        ;;
    --help)
        echo "Usage: $0 <backup_file> | --list | --latest"
        echo ""
        echo "Restore a database backup to the UNS-Kobetsu system."
        echo ""
        echo "Options:"
        echo "  backup_file    Path to backup file to restore"
        echo "  --list         List available backups"
        echo "  --latest       Restore the most recent backup"
        echo "  --help         Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 ./backups/kobetsu_backup_20241129_120000.sql.gz"
        echo "  $0 --latest"
        exit 0
        ;;
    *)
        BACKUP_FILE="$1"
        ;;
esac

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}=== UNS-Kobetsu Database Restore ===${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}Error: Database container '$DB_CONTAINER' is not running${NC}"
    echo "Please start the container with: docker compose up -d"
    exit 1
fi

# Verify backup file integrity
echo "Verifying backup file..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ Backup file is valid${NC}"
else
    echo -e "${RED}✗ Backup file is corrupted${NC}"
    exit 1
fi

# Show backup metadata if available
META_FILE="${BACKUP_FILE%.sql.gz}.meta"
if [ -f "$META_FILE" ]; then
    echo ""
    echo "Backup metadata:"
    cat "$META_FILE" | sed 's/^/  /'
    echo ""
fi

# Get current database statistics
echo "Current database statistics:"
CURRENT_SIZE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT pg_size_pretty(pg_database_size('$DB_NAME'))" 2>/dev/null | xargs || echo "Unknown")
CURRENT_CONTRACTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM kobetsu_keiyakusho" 2>/dev/null | xargs || echo "0")
CURRENT_EMPLOYEES=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM employees" 2>/dev/null | xargs || echo "0")

echo "  Database size: $CURRENT_SIZE"
echo "  Contracts: $CURRENT_CONTRACTS"
echo "  Employees: $CURRENT_EMPLOYEES"
echo ""

# Confirmation prompt
echo -e "${YELLOW}WARNING: This will replace all data in the database!${NC}"
read -p "Are you sure you want to restore this backup? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Create safety backup before restore
echo ""
echo "Creating safety backup of current database..."
SAFETY_BACKUP="${BACKUP_DIR}/kobetsu_safety_$(date +%Y%m%d_%H%M%S).sql.gz"
if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip -9 > "$SAFETY_BACKUP" 2>/dev/null; then
    echo -e "${GREEN}✓ Safety backup created: $SAFETY_BACKUP${NC}"
else
    echo -e "${YELLOW}⚠ Could not create safety backup (database might be empty)${NC}"
fi

# Perform the restore
echo ""
echo "Restoring database..."

# Drop existing connections to the database
echo "Closing existing connections..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true

# Restore the backup
if gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d postgres >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}✗ Restore failed${NC}"
    if [ -f "$SAFETY_BACKUP" ]; then
        echo "You can restore the safety backup with:"
        echo "  $0 $SAFETY_BACKUP"
    fi
    exit 1
fi

# Verify the restore
echo ""
echo "Verifying restored database..."
RESTORED_SIZE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT pg_size_pretty(pg_database_size('$DB_NAME'))" 2>/dev/null | xargs || echo "Unknown")
RESTORED_CONTRACTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM kobetsu_keiyakusho" 2>/dev/null | xargs || echo "0")
RESTORED_EMPLOYEES=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM employees" 2>/dev/null | xargs || echo "0")

echo "Restored database statistics:"
echo "  Database size: $RESTORED_SIZE"
echo "  Contracts: $RESTORED_CONTRACTS"
echo "  Employees: $RESTORED_EMPLOYEES"

# Restart backend to clear any cached connections
echo ""
echo "Restarting backend service..."
if docker compose restart backend >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend service restarted${NC}"
else
    echo -e "${YELLOW}⚠ Could not restart backend service. Please restart manually.${NC}"
fi

echo ""
echo -e "${GREEN}=== Database restore completed successfully ===${NC}"
echo "The database has been restored from: $(basename "$BACKUP_FILE")"

if [ -f "$SAFETY_BACKUP" ]; then
    echo ""
    echo "A safety backup of the previous database was saved to:"
    echo "  $SAFETY_BACKUP"
fi