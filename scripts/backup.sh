#!/bin/bash

#############################################################################
# Database Backup Script for UNS-Kobetsu System
#
# Usage:
#   ./scripts/backup.sh                     # Backup with default settings
#   ./scripts/backup.sh --keep 14           # Keep 14 days of backups
#   ./scripts/backup.sh --dir /custom/path  # Custom backup directory
#
# Features:
#   - Creates timestamped backups
#   - Automatically removes old backups (default: keep last 7)
#   - Compresses backups with gzip
#   - Includes database statistics in backup
#############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"
DB_CONTAINER="uns-kobetsu-db"
DB_NAME="${POSTGRES_DB:-kobetsu_db}"
DB_USER="${POSTGRES_USER:-kobetsu_admin}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep)
            KEEP_DAYS="$2"
            shift 2
            ;;
        --dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --keep N     Keep N days of backups (default: 7)"
            echo "  --dir PATH   Backup directory (default: ./backups)"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp for backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/kobetsu_backup_${TIMESTAMP}.sql.gz"
META_FILE="${BACKUP_DIR}/kobetsu_backup_${TIMESTAMP}.meta"

echo -e "${GREEN}=== UNS-Kobetsu Database Backup ===${NC}"
echo "Timestamp: $(date)"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}Error: Database container '$DB_CONTAINER' is not running${NC}"
    echo "Please start the container with: docker compose up -d"
    exit 1
fi

# Get database statistics before backup
echo "Collecting database statistics..."
DB_SIZE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT pg_size_pretty(pg_database_size('$DB_NAME'))" 2>/dev/null | xargs || echo "Unknown")

TABLE_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'" 2>/dev/null | xargs || echo "0")

# Get row counts for main tables
CONTRACT_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM kobetsu_keiyakusho" 2>/dev/null | xargs || echo "0")

EMPLOYEE_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM employees" 2>/dev/null | xargs || echo "0")

FACTORY_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM factories" 2>/dev/null | xargs || echo "0")

# Save metadata
cat > "$META_FILE" <<EOF
Backup Timestamp: $(date)
Database: $DB_NAME
Database Size: $DB_SIZE
Tables: $TABLE_COUNT
Contracts: $CONTRACT_COUNT
Employees: $EMPLOYEE_COUNT
Factories: $FACTORY_COUNT
Host: $(hostname)
Docker Container: $DB_CONTAINER
EOF

echo "Database size: $DB_SIZE"
echo "Tables: $TABLE_COUNT"
echo "Records - Contracts: $CONTRACT_COUNT, Employees: $EMPLOYEE_COUNT, Factories: $FACTORY_COUNT"
echo ""

# Perform the backup
echo "Creating backup..."
if docker exec "$DB_CONTAINER" pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --no-owner \
    --no-privileges \
    --no-comments \
    | gzip -9 > "$BACKUP_FILE" 2>/dev/null; then

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup created successfully${NC}"
    echo "  File: $BACKUP_FILE"
    echo "  Size: $BACKUP_SIZE"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# Verify backup file
echo ""
echo "Verifying backup..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ Backup file is valid${NC}"
else
    echo -e "${RED}✗ Backup file is corrupted${NC}"
    exit 1
fi

# Clean up old backups
echo ""
echo "Cleaning up old backups (keeping last $KEEP_DAYS days)..."
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "kobetsu_backup_*.sql.gz" -type f -mtime +$KEEP_DAYS)
if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read -r file; do
        echo "  Removing: $(basename "$file")"
        rm -f "$file"
        # Also remove metadata file
        META="${file%.sql.gz}.meta"
        [ -f "$META" ] && rm -f "$META"
    done
    echo -e "${YELLOW}Old backups removed${NC}"
else
    echo "No old backups to remove"
fi

# List current backups
echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR"/kobetsu_backup_*.sql.gz 2>/dev/null | tail -5 | while read -r line; do
    echo "  $line"
done

echo ""
echo -e "${GREEN}=== Backup completed successfully ===${NC}"
echo "To restore this backup, use:"
echo "  ./scripts/restore.sh $BACKUP_FILE"