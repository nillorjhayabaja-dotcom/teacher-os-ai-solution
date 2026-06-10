#!/bin/bash
# =============================================================================
# TeacherOS - Backup Script
# =============================================================================
# Usage:
#   ./docker/scripts/backup.sh                   # Full backup
#   ./docker/scripts/backup.sh --db-only         # Database only
#   ./docker/scripts/backup.sh --storage-only    # MinIO only
#   ./docker/scripts/backup.sh --restore <file>  # Restore from backup
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
BACKUP_DIR="${BACKUP_DIR:-./data/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="teacheros_backup_${TIMESTAMP}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
DATE_FORMAT="+%Y-%m-%d %H:%M:%S"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date "$DATE_FORMAT") - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date "$DATE_FORMAT") - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date "$DATE_FORMAT") - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date "$DATE_FORMAT") - $1"
}

check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

check_container() {
    local container="$1"
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        log_warning "Container ${container} is not running. Skipping..."
        return 1
    fi
    return 0
}

# =============================================================================
# Backup Functions
# =============================================================================
backup_postgres() {
    log_info "Starting PostgreSQL backup..."
    
    mkdir -p "${BACKUP_DIR}/postgres"
    
    local container="teacheros-postgres"
    if check_container "$container"; then
        local db="${POSTGRES_DB:-teacheros}"
        local user="${POSTGRES_USER:-teacheros}"
        local backup_file="${BACKUP_DIR}/postgres/${BACKUP_NAME}.sql.gz"
        
        docker exec "$container" pg_dump -U "$user" -d "$db" --clean --if-exists --no-owner | gzip > "$backup_file"
        
        if [ $? -eq 0 ] && [ -s "$backup_file" ]; then
            log_success "PostgreSQL backup saved: ${backup_file}"
            echo "$backup_file" >> "${BACKUP_DIR}/latest_postgres_backup.txt"
        else
            log_error "PostgreSQL backup failed"
            rm -f "$backup_file"
            return 1
        fi
    fi
}

backup_redis() {
    log_info "Starting Redis backup..."
    
    mkdir -p "${BACKUP_DIR}/redis"
    
    local container="teacheros-redis"
    if check_container "$container"; then
        local backup_file="${BACKUP_DIR}/redis/${BACKUP_NAME}.rdb"
        local aof_backup="${BACKUP_DIR}/redis/${BACKUP_NAME}.aof.gz"
        
        # Trigger SAVE
        docker exec "$container" redis-cli SAVE
        
        # Copy RDB file
        docker cp "$container:/data/dump.rdb" "$backup_file"
        
        # Copy AOF if exists
        docker exec "$container" redis-cli BGREWRITEAOF || true
        sleep 2
        
        if [ -s "$backup_file" ]; then
            log_success "Redis backup saved: ${backup_file}"
            echo "$backup_file" >> "${BACKUP_DIR}/latest_redis_backup.txt"
        else
            log_warning "Redis backup file empty"
        fi
    fi
}

backup_minio() {
    log_info "Starting MinIO backup..."
    
    mkdir -p "${BACKUP_DIR}/minio"
    
    local container="teacheros-storage"
    if check_container "$container"; then
        local backup_file="${BACKUP_DIR}/minio/${BACKUP_NAME}.tar.gz"
        
        # Backup MinIO data directory
        docker run --rm --volumes-from "$container" \
            -v "${BACKUP_DIR}/minio:/backup" \
            alpine:3.21 tar czf "/backup/${BACKUP_NAME}.tar.gz" -C /data .
        
        if [ -s "$backup_file" ]; then
            log_success "MinIO backup saved: ${backup_file}"
            echo "$backup_file" >> "${BACKUP_DIR}/latest_minio_backup.txt"
        else
            log_error "MinIO backup failed"
            rm -f "$backup_file"
            return 1
        fi
    fi
}

backup_config() {
    log_info "Starting configuration backup..."
    
    mkdir -p "${BACKUP_DIR}/config"
    
    local backup_file="${BACKUP_DIR}/config/${BACKUP_NAME}.tar.gz"
    
    # Backup configuration files (exclude .env files containing secrets)
    tar czf "$backup_file" \
        -C . \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='data' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.env.*' \
        docker-compose*.yml docker/ infra/ nginx/ 2>/dev/null || true
    
    if [ -s "$backup_file" ]; then
        log_success "Configuration backup saved: ${backup_file}"
    else
        log_warning "No configuration files to backup"
    fi
}

# =============================================================================
# Restore Functions
# =============================================================================
restore_postgres() {
    local backup_file="$1"
    log_info "Restoring PostgreSQL from: ${backup_file}"
    
    local container="teacheros-postgres"
    if check_container "$container"; then
        local db="${POSTGRES_DB:-teacheros}"
        local user="${POSTGRES_USER:-teacheros}"
        
        # Drop and recreate database
        docker exec "$container" psql -U "$user" -c "DROP DATABASE IF EXISTS ${db};"
        docker exec "$container" psql -U "$user" -c "CREATE DATABASE ${db};"
        
        # Restore from backup
        gunzip -c "$backup_file" | docker exec -i "$container" psql -U "$user" -d "$db"
        
        if [ $? -eq 0 ]; then
            log_success "PostgreSQL restore complete"
        else
            log_error "PostgreSQL restore failed"
            return 1
        fi
    fi
}

restore_minio() {
    local backup_file="$1"
    log_info "Restoring MinIO from: ${backup_file}"
    
    local container="teacheros-storage"
    if check_container "$container"; then
        docker run --rm --volumes-from "$container" \
            -v "${BACKUP_DIR}/minio:/backup" \
            alpine:3.21 tar xzf "/backup/$(basename "$backup_file")" -C /data
        
        log_success "MinIO restore complete"
    fi
}

# =============================================================================
# Cleanup Old Backups
# =============================================================================
cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
    
    find "${BACKUP_DIR}/postgres" -name "*.sql.gz" -type f -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${BACKUP_DIR}/redis" -name "*.rdb" -type f -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${BACKUP_DIR}/minio" -name "*.tar.gz" -type f -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${BACKUP_DIR}/config" -name "*.tar.gz" -type f -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    
    log_success "Cleanup complete"
}

# =============================================================================
# Main
# =============================================================================
main() {
    mkdir -p "${BACKUP_DIR}"/{postgres,redis,minio,config}
    
    local mode="${1:-full}"
    local restore_file="${2:-}"
    
    case "$mode" in
        --db-only)
            check_docker
            backup_postgres
            ;;
        --redis-only)
            check_docker
            backup_redis
            ;;
        --storage-only)
            check_docker
            backup_minio
            ;;
        --config-only)
            backup_config
            ;;
        --full)
            check_docker
            backup_postgres
            backup_redis
            backup_minio
            backup_config
            cleanup_old_backups
            log_success "Full backup completed successfully!"
            ;;
        --restore)
            if [ -z "$restore_file" ]; then
                log_error "Please specify backup file to restore"
                echo "Usage: $0 --restore <backup_file>"
                exit 1
            fi
            check_docker
            case "$restore_file" in
                *postgres*|*.sql.gz)
                    restore_postgres "$restore_file"
                    ;;
                *minio*|*.tar.gz)
                    restore_minio "$restore_file"
                    ;;
                *)
                    log_error "Unknown backup type: ${restore_file}"
                    exit 1
                    ;;
            esac
            ;;
        --list)
            echo "=== PostgreSQL Backups ==="
            ls -lh "${BACKUP_DIR}/postgres/" 2>/dev/null || echo "No backups"
            echo "=== Redis Backups ==="
            ls -lh "${BACKUP_DIR}/redis/" 2>/dev/null || echo "No backups"
            echo "=== MinIO Backups ==="
            ls -lh "${BACKUP_DIR}/minio/" 2>/dev/null || echo "No backups"
            echo "=== Config Backups ==="
            ls -lh "${BACKUP_DIR}/config/" 2>/dev/null || echo "No backups"
            ;;
        *)
            echo "TeacherOS Backup Script"
            echo "======================="
            echo "Usage:"
            echo "  $0                    Full backup (all services)"
            echo "  $0 --db-only          Database only"
            echo "  $0 --redis-only       Redis only"
            echo "  $0 --storage-only     MinIO only"
            echo "  $0 --config-only      Configuration files"
            echo "  $0 --full             Full backup (same as no argument)"
            echo "  $0 --restore <file>   Restore from backup file"
            echo "  $0 --list             List available backups"
            echo ""
            echo "Environment Variables:"
            echo "  BACKUP_DIR            Backup directory (default: ./data/backups)"
            echo "  BACKUP_RETENTION_DAYS Days to keep backups (default: 30)"
            echo "  POSTGRES_DB           Database name"
            echo "  POSTGRES_USER         Database user"
            ;;
    esac
}

main "$@"