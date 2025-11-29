# UNS-Kobetsu Scripts Directory

This directory contains utility scripts for managing the UNS-Kobetsu system.

## 📋 Available Scripts

### System Management

#### `init-local.sh`
Initializes the local development environment.

```bash
# Standard initialization
../init-local.sh

# Reset everything (CAUTION: Data loss!)
../init-local.sh --reset

# Start with log following
../init-local.sh --logs

# Skip health checks for faster startup
../init-local.sh --quick

# Import demo data after startup
../init-local.sh --import-demo
```

#### `cleanup.sh`
Cleans up system resources to free disk space.

```bash
# Run all cleanup tasks
./cleanup.sh

# Clean only specific resources
./cleanup.sh --logs       # Clean only logs
./cleanup.sh --docker     # Clean only Docker resources
./cleanup.sh --temp       # Clean only temporary files

# Preview what would be cleaned
./cleanup.sh --dry-run

# Keep different number of days for logs
./cleanup.sh --days 14
```

### Database Management

#### `backup.sh`
Creates timestamped backups of the database.

```bash
# Create backup with default settings (keeps 7 days)
./backup.sh

# Keep backups for 14 days
./backup.sh --keep 14

# Use custom backup directory
./backup.sh --dir /custom/backup/path
```

**Features:**
- Creates compressed backups (.sql.gz)
- Includes metadata (size, record counts)
- Automatically removes old backups
- Verifies backup integrity

#### `restore.sh`
Restores database from a backup file.

```bash
# List available backups
./restore.sh --list

# Restore specific backup
./restore.sh ./backups/kobetsu_backup_20241129_120000.sql.gz

# Restore latest backup
./restore.sh --latest
```

**Features:**
- Creates safety backup before restore
- Shows backup metadata before confirmation
- Verifies backup integrity
- Restarts backend after restore

### Testing & Verification

#### `test_new_endpoints.sh`
Tests the health and statistics endpoints.

```bash
./test_new_endpoints.sh
```

Tests:
- `/api/v1/health/basic` - Basic health check
- `/api/v1/health/detailed` - Detailed health with dependencies
- `/api/v1/health/ready` - Readiness check
- `/api/v1/health/live` - Liveness check
- `/api/v1/stats/system` - System resources
- `/api/v1/stats/app` - Application statistics
- `/api/v1/stats/database` - Database metrics
- `/api/v1/stats/usage` - Usage trends

#### `verify_setup.py`
Python script to verify backend setup.

```bash
docker exec uns-kobetsu-backend python scripts/verify_setup.py
```

Checks:
- Import dependencies
- Configuration settings
- Database connection
- Migration status

### Data Management

#### `create_admin.py`
Creates an admin user account.

```bash
docker exec uns-kobetsu-backend python scripts/create_admin.py
```

Default credentials:
- Email: admin@uns-kobetsu.com
- Password: admin123

#### `import_demo_data.py`
Imports sample data for testing.

```bash
docker exec uns-kobetsu-backend python scripts/import_demo_data.py
```

Creates:
- Sample factories
- Sample employees
- Sample contracts

## 🔒 Security Notes

1. **Backup Security**: Backup files contain sensitive data. Store them securely and encrypt if necessary.

2. **Reset Mode**: The `--reset` flag in `init-local.sh` will DELETE ALL DATA. Use with extreme caution.

3. **Production**: These scripts are designed for development. For production:
   - Use proper backup solutions
   - Implement encryption for backups
   - Use secure credential management
   - Set appropriate file permissions

## 🛠️ Troubleshooting

### Scripts not executable
```bash
chmod +x *.sh
```

### Docker not found
Ensure Docker and Docker Compose are installed and running.

### Database connection errors
```bash
# Check if containers are running
docker compose ps

# Check database logs
docker compose logs db
```

### Backup/Restore issues
```bash
# Check database container name
docker ps | grep postgres

# Verify database credentials
docker exec uns-kobetsu-db psql -U kobetsu_admin -l
```

## 📝 Script Development Guidelines

When creating new scripts:

1. **Use consistent style**:
   - Color codes for output
   - Clear section headers
   - Error handling with `set -e`

2. **Add help text**:
   - Include `--help` option
   - Document all parameters
   - Provide usage examples

3. **Safety first**:
   - Confirm destructive operations
   - Create backups before modifications
   - Use dry-run mode when applicable

4. **Make executable**:
   ```bash
   chmod +x new_script.sh
   ```

5. **Test thoroughly**:
   - Test all code paths
   - Test error conditions
   - Test with different parameters

## 📚 Related Documentation

- [Project README](../README.md)
- [CLAUDE.md](../CLAUDE.md)
- [Backend Documentation](../backend/README.md)
- [API Documentation](http://localhost:8010/docs)