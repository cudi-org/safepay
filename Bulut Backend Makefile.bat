# Bulut Backend Makefile
# Quick commands for development and deployment

.PHONY: help install dev test lint format clean docker-build docker-up deploy-cloudflare

# Default target
help:
	@echo "Bulut Backend - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install dependencies"
	@echo "  make dev              - Run development server"
	@echo "  make test             - Run test suite"
	@echo "  make test-cov         - Run tests with coverage"
	@echo "  make lint             - Run linting"
	@echo "  make format           - Format code"
	@echo ""
	@echo "Database:"
	@echo "  make db-init          - Initialize database"
	@echo "  make db-migrate       - Run migrations"
	@echo "  make db-reset         - Reset database"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-up        - Start Docker containers"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-cloudflare - Deploy to Cloudflare Workers"
	@echo "  make deploy-staging   - Deploy to staging"
	@echo "  make deploy-prod      - Deploy to production"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Clean temporary files"
	@echo "  make check            - Run all checks"
	@echo ""

# ============================================================================
# DEVELOPMENT
# ============================================================================

install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "✅ Dependencies installed"

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "✅ Development dependencies installed"

dev:
	@echo "🚀 Starting development server..."
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-debug:
	@echo "🐛 Starting development server with debug logging..."
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "🧪 Running test suite..."
	pytest test_backend.py -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest test_backend.py -v --cov=. --cov-report=html --cov-report=term

test-watch:
	@echo "🔄 Running tests in watch mode..."
	pytest-watch test_backend.py -v

# ============================================================================
# CODE QUALITY
# ============================================================================

lint:
	@echo "🔍 Running linters..."
	flake8 . --max-line-length=100 --exclude=venv,__pycache__
	mypy . --ignore-missing-imports
	@echo "✅ Linting complete"

format:
	@echo "✨ Formatting code..."
	black . --line-length=100
	isort . --profile black
	@echo "✅ Code formatted"

check: lint test
	@echo "✅ All checks passed"

# ============================================================================
# DATABASE
# ============================================================================

db-init:
	@echo "🗄️  Initializing database..."
	python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
	@echo "✅ Database initialized"

db-migrate:
	@echo "🔄 Running migrations..."
	alembic upgrade head
	@echo "✅ Migrations complete"

db-reset:
	@echo "⚠️  Resetting database..."
	@read -p "Are you sure? This will delete all data! (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		rm -f bulut.db; \
		make db-init; \
	fi

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built"

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Containers started"
	@echo "📍 Backend: http://localhost:8000"
	@echo "📍 AI Agent: http://localhost:8001"
	@echo "📍 Docs: http://localhost:8000/docs"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped"

docker-logs:
	@echo "📋 Docker logs..."
	docker-compose logs -f

docker-restart:
	@echo "🔄 Restarting Docker containers..."
	docker-compose restart
	@echo "✅ Containers restarted"

docker-clean:
	@echo "🧹 Cleaning Docker..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Docker cleaned"

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy-cloudflare:
	@echo "☁️  Deploying to Cloudflare Workers..."
	wrangler publish
	@echo "✅ Deployed to Cloudflare"

deploy-staging:
	@echo "🚀 Deploying to staging..."
	wrangler publish --env staging
	@echo "✅ Deployed to staging"

deploy-prod:
	@echo "🚀 Deploying to production..."
	@read -p "Deploy to PRODUCTION? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		wrangler publish --env production; \
		echo "✅ Deployed to production"; \
	fi

# ============================================================================
# UTILITIES
# ============================================================================

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .coverage htmlcov/
	@echo "✅ Cleaned"

requirements:
	@echo "📝 Generating requirements.txt..."
	pip freeze > requirements.txt
	@echo "✅ Requirements generated"

env:
	@echo "📋 Creating .env file from example..."
	cp .env.example .env
	@echo "✅ .env file created - please update with your values"

setup: install env db-init
	@echo "✅ Initial setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Update .env with your API keys"
	@echo "2. Run 'make dev' to start the server"
	@echo "3. Visit http://localhost:8000/docs"

# ============================================================================
# MONITORING
# ============================================================================

logs:
	@echo "📋 Showing application logs..."
	tail -f logs/bulut.log

health-check:
	@echo "🏥 Checking application health..."
	curl -s http://localhost:8000/health | jq .

api-test:
	@echo "🔬 Testing API endpoints..."
	@echo "\n1. Health Check:"
	curl -s http://localhost:8000/health | jq .
	@echo "\n2. Root Endpoint:"
	curl -s http://localhost:8000/ | jq .

# ============================================================================
# BENCHMARKING
# ============================================================================

benchmark:
	@echo "⚡ Running performance benchmarks..."
	ab -n 1000 -c 10 http://localhost:8000/health
	@echo "✅ Benchmark complete"

load-test:
	@echo "💪 Running load tests..."
	locust -f tests/locustfile.py --headless -u 100 -r 10 -t 60s
	@echo "✅ Load test complete"