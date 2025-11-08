#!/bin/bash
# Database Import Script for VPS Production/Test Environment
# Usage: ./db_import_vps.sh [backup_file]
# This script imports a backup file into a fresh database on VPS

set -e  # Exit on error

# VPS Production Database Configuration
DB_NAME="pola_db"
DB_USER="polaadmin"
DB_PASSWORD="1234"
DB_HOST="localhost"
DB_PORT="5432"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to check if PostgreSQL is installed
check_postgresql() {
    print_info "Checking PostgreSQL installation..."
    
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL is not installed!"
        echo ""
        echo "Install PostgreSQL on Ubuntu/Debian:"
        echo "  sudo apt update"
        echo "  sudo apt install postgresql postgresql-contrib"
        echo ""
        echo "Install PostgreSQL on CentOS/RHEL:"
        echo "  sudo yum install postgresql-server postgresql-contrib"
        echo "  sudo postgresql-setup initdb"
        echo "  sudo systemctl start postgresql"
        exit 1
    fi
    
    print_success "PostgreSQL is installed"
}

# Function to check if database exists
check_database() {
    print_info "Checking if database '$DB_NAME' exists..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        print_success "Database '$DB_NAME' exists"
        return 0
    else
        print_warning "Database '$DB_NAME' does not exist"
        return 1
    fi
}

# Function to create database and user
setup_database() {
    print_info "Setting up database and user..."
    
    # Switch to postgres superuser to create database and user
    print_info "Creating database '$DB_NAME' and user '$DB_USER'..."
    
    sudo -u postgres psql <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Grant schema privileges
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

    if [ $? -eq 0 ]; then
        print_success "Database and user setup complete"
    else
        print_error "Failed to setup database and user"
        exit 1
    fi
}

# Function to check if database has data
check_database_empty() {
    print_info "Checking if database is empty..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    TABLE_COUNT=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null || echo "0")
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        print_warning "Database already has $TABLE_COUNT tables"
        echo ""
        read -p "$(echo -e ${YELLOW}Do you want to DROP all existing data and import fresh? [y/N]:${NC} )" -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Import cancelled. Database has existing data."
            exit 1
        fi
        return 1
    else
        print_success "Database is empty and ready for import"
        return 0
    fi
}

# Function to import database from backup
import_database() {
    local BACKUP_FILE=$1
    
    # Verify backup file exists
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    print_info "Backup file: $BACKUP_FILE"
    print_info "Backup size: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"
    
    # Show backup info
    print_info "Backup contains:"
    pg_restore -l "$BACKUP_FILE" | grep "TABLE\|SEQUENCE\|INDEX" | head -10
    echo "..."
    
    # Set password for import
    export PGPASSWORD="$DB_PASSWORD"
    
    print_info "Importing database from backup..."
    echo ""
    
    # Import with clean option to handle existing objects
    pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-acl "$BACKUP_FILE" 2>&1 | tee /tmp/import.log
    
    # Check if import was successful (pg_restore returns 0 even with warnings)
    if grep -q "ERROR" /tmp/import.log; then
        print_error "Import completed with errors. Check /tmp/import.log"
        echo ""
        read -p "Do you want to continue anyway? [y/N]: " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "Database import completed!"
    
    # Verify import
    print_info "Verifying import..."
    TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
    
    print_success "Imported $TABLE_COUNT tables"
}

# Function to update database permissions
fix_permissions() {
    print_info "Fixing database permissions..."
    
    export PGPASSWORD="$DB_PASSWORD"
    
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
-- Grant all privileges on all tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;

-- Grant all privileges on all sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- Grant all privileges on all functions
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;
EOF

    print_success "Permissions fixed"
}

# Function to show database info
show_database_info() {
    print_info "Database Information:"
    echo ""
    
    export PGPASSWORD="$DB_PASSWORD"
    
    echo "Database Size:"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME')) as size;"
    
    echo ""
    echo "Table Count:"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
    
    echo ""
    echo "Top 10 Largest Tables:"
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT schemaname as schema, tablename as table, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
}

# Main script
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║     Pola Database Import Script - VPS Production      ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check if backup file is provided
    if [ -z "$1" ]; then
        print_error "No backup file specified!"
        echo ""
        echo "Usage: $0 <backup_file>"
        echo ""
        echo "Examples:"
        echo "  $0 ./pola_settings/pola_db_backup_20251108_163735.backup"
        echo "  $0 /tmp/pola_backup.backup"
        echo ""
        exit 1
    fi
    
    BACKUP_FILE=$1
    
    # Run checks and setup
    check_postgresql
    
    # Check if database exists
    if ! check_database; then
        echo ""
        print_warning "Database setup required"
        read -p "Do you want to create database '$DB_NAME' and user '$DB_USER'? [Y/n]: " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            print_error "Database setup cancelled. Cannot proceed with restore."
            exit 1
        fi
        
        setup_database
    fi
    
    echo ""
    
    # Check if database is empty
    check_database_empty
    
    echo ""
    
    # Import database from backup
    import_database "$BACKUP_FILE"
    
    echo ""
    
    # Fix permissions
    fix_permissions
    
    echo ""
    
    # Show database info
    show_database_info
    
    echo ""
    print_success "All done! Database '$DB_NAME' has been imported successfully."
    echo ""
    print_info "Connection details:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo ""
    print_info "Update your Django .env file on VPS with:"
    echo "  DB_NAME=$DB_NAME"
    echo "  DB_USER=$DB_USER"
    echo "  DB_PASSWORD=$DB_PASSWORD"
    echo "  DB_HOST=$DB_HOST"
    echo "  DB_PORT=$DB_PORT"
    echo ""
    print_info "Next steps:"
    echo "  1. Update .env file with database credentials"
    echo "  2. Run: python manage.py migrate"
    echo "  3. Run: python manage.py collectstatic"
    echo "  4. Restart your Django application"
    echo ""
}

# Run main function
main "$@"
