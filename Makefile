# ==========================================
# Makefile for POLA Backend Docker Commands
# ==========================================
# Usage: make <command>
# ==========================================

.PHONY: help build up down logs shell migrate test clean prod-up prod-down prod-logs backup restore

# Default target
help:
	@echo "POLA Backend Docker Commands"
	@echo ""
	@echo "Local Development:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs (follow mode)"
	@echo "  make shell        - Open Django shell"
	@echo "  make bash         - Open bash in web container"
	@echo "  make migrate      - Run database migrations"
	@echo "  make makemigrations - Create new migrations"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove all containers and volumes"
	@echo ""
	@echo "Production:"
	@echo "  make prod-build   - Build production images"
	@echo "  make prod-up      - Start production services"
	@echo "  make prod-down    - Stop production services"
	@echo "  make prod-logs    - View production logs"
	@echo "  make init-ssl     - Initialize SSL certificates"
	@echo ""
	@echo "Database:"
	@echo "  make backup       - Backup local database"
	@echo "  make backup-prod  - Backup production database"
	@echo "  make dbshell      - Open PostgreSQL shell"

# ==========================================
# Local Development Commands
# ==========================================

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "Services started! Access the API at http://localhost:8000"
	@echo "View logs with: make logs"

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec web python manage.py shell

bash:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

test:
	docker-compose exec web python manage.py test

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

dbshell:
	docker-compose exec db psql -U $${DB_USER:-pola_user} -d $${DB_NAME:-pola_db}

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

restart:
	docker-compose restart

rebuild:
	docker-compose up -d --build

# ==========================================
# Production Commands
# ==========================================

prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d
	@echo ""
	@echo "Production services started!"

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

prod-shell:
	docker-compose -f docker-compose.prod.yml exec web python manage.py shell

prod-migrate:
	docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

prod-restart:
	docker-compose -f docker-compose.prod.yml restart

init-ssl:
	chmod +x scripts/init-ssl.sh
	./scripts/init-ssl.sh

# ==========================================
# Database Backup Commands
# ==========================================

backup:
	chmod +x scripts/backup-db.sh
	./scripts/backup-db.sh local

backup-prod:
	chmod +x scripts/backup-db.sh
	./scripts/backup-db.sh production

# ==========================================
# Development Utilities
# ==========================================

# Install dependencies locally (for IDE support)
install-local:
	pip install -r requirements.txt

# Format code
format:
	docker-compose exec web black .
	docker-compose exec web isort .

# Check code style
lint:
	docker-compose exec web flake8 .

# Show running containers
ps:
	docker-compose ps

# Show container resource usage
stats:
	docker stats --no-stream
