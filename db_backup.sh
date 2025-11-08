#!/bin/bash
# Database Backup Script for Pola Backend
# Usage: ./db_backup.sh [backup|restore]

# Configuration
export PATH="/Library/PostgreSQL/15/bin:$PATH"
export PGPASSWORD='root'
DB_NAME="pola_db_v1"
DB_USER="postgres"
DB_HOST="127.0.0.1"
DB_PORT="5432"
BACKUP_DIR="./pola_settings"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to create backup
backup_database() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/pola_db_backup_${TIMESTAMP}.backup"
    
    echo -e "${YELLOW}Creating database backup...${NC}"
    
    pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -Fc -f "$BACKUP_FILE" "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
        echo -e "${GREEN}✅ Backup created successfully!${NC}"
        echo -e "   File: $BACKUP_FILE"
        echo -e "   Size: $SIZE"
        
        # List recent backups
        echo -e "\n${YELLOW}Recent backups:${NC}"
        ls -lht ${BACKUP_DIR}/*.backup | head -5
    else
        echo -e "${RED}❌ Backup failed!${NC}"
        exit 1
    fi
}

# Function to restore database
restore_database() {
    # Find the latest backup if no file specified
    if [ -z "$1" ]; then
        BACKUP_FILE=$(ls -t ${BACKUP_DIR}/*.backup 2>/dev/null | head -1)
        if [ -z "$BACKUP_FILE" ]; then
            echo -e "${RED}❌ No backup files found!${NC}"
            exit 1
        fi
        echo -e "${YELLOW}Using latest backup: $BACKUP_FILE${NC}"
    else
        BACKUP_FILE="$1"
    fi
    
    # Verify backup file exists
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
        exit 1
    fi
    
    # Show backup info
    echo -e "${YELLOW}Backup file info:${NC}"
    pg_restore -l "$BACKUP_FILE" | head -15
    
    # Ask for confirmation
    read -p "Do you want to restore this backup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Restore cancelled.${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}Restoring database...${NC}"
    
    # Restore with clean option (drop existing objects first)
    pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database restored successfully!${NC}"
    else
        echo -e "${RED}⚠️  Restore completed with warnings (this is normal)${NC}"
    fi
}

# Function to list backups
list_backups() {
    echo -e "${YELLOW}Available backups:${NC}"
    ls -lht ${BACKUP_DIR}/*.backup 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}No backup files found!${NC}"
    fi
}

# Main script logic
case "$1" in
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    list)
        list_backups
        ;;
    *)
        echo -e "${YELLOW}Database Backup & Restore Tool${NC}"
        echo ""
        echo "Usage:"
        echo "  ./db_backup.sh backup              - Create a new backup"
        echo "  ./db_backup.sh restore             - Restore latest backup"
        echo "  ./db_backup.sh restore <file>      - Restore specific backup file"
        echo "  ./db_backup.sh list                - List all backups"
        echo ""
        echo "Examples:"
        echo "  ./db_backup.sh backup"
        echo "  ./db_backup.sh restore"
        echo "  ./db_backup.sh restore ./pola_settings/pola_db_backup_20251108_163735.backup"
        echo "  ./db_backup.sh list"
        exit 1
        ;;
esac
