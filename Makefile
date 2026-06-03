.PHONY: help dev serve test test-unit test-integration test-e2e lint format build \
        migrate migrate-down infra-up infra-down stack-up stack-down clean setup

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# ── Desarrollo ──────────────────────────────────────────────────────────────

dev: ## Levantar servidor en modo desarrollo con hot-reload
	# TODO: reemplazar con el comando del stack
	# ej. poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
	# ej. go run ./cmd/server
	# ej. npm run dev
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

serve: ## Levantar servidor en modo producción
	# TODO: reemplazar con el comando del stack
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

# ── Tests ─────────────────────────────────────────────────────────────────────

test: ## Ejecutar todos los tests con cobertura
	# TODO: ej. poetry run pytest --cov --cov-fail-under=97 -v
	# ej. go test ./... -cover
	# ej. npm run test -- --coverage
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

test-unit: ## Ejecutar solo tests unitarios
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

test-integration: ## Ejecutar solo tests de integración
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

test-e2e: ## Ejecutar tests end-to-end
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

test-no-cov: ## Ejecutar tests sin reporte de cobertura (más rápido)
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

# ── Calidad ──────────────────────────────────────────────────────────────────

lint: ## Verificar estilo y calidad del código
	# TODO: ej. poetry run ruff check .
	# ej. golangci-lint run
	# ej. npm run lint
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

format: ## Formatear código automáticamente
	# TODO: ej. poetry run ruff format .
	# ej. gofmt -w .
	# ej. npm run format
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

lint-fix: ## Aplicar correcciones automáticas de lint
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

# ── Base de datos ─────────────────────────────────────────────────────────────

migrate: ## Aplicar migraciones pendientes
	@echo "→ Configura este comando si el proyecto usa migraciones"

migrate-down: ## Revertir la última migración
	@echo "→ Configura este comando si el proyecto usa migraciones"

migrate-reset: ## Revertir y volver a aplicar todas las migraciones
	@echo "→ Configura este comando si el proyecto usa migraciones"

# ── Infraestructura local ─────────────────────────────────────────────────────

infra-up: ## Levantar servicios de infraestructura (DB, cache, etc.)
	docker compose -f docker-compose.dev.yml up -d

infra-down: ## Detener servicios de infraestructura
	docker compose -f docker-compose.dev.yml down

infra-logs: ## Ver logs de infraestructura
	docker compose -f docker-compose.dev.yml logs -f

stack-up: ## Levantar el stack completo en producción local
	docker compose up -d

stack-down: ## Detener el stack completo
	docker compose down

# ── Docker ───────────────────────────────────────────────────────────────────

build: ## Construir imagen Docker
	docker build -t {PROJECT_NAME}:local .

# ── Utilidades ────────────────────────────────────────────────────────────────

install: ## Instalar dependencias del proyecto
	# TODO: ej. poetry install
	# ej. go mod download
	# ej. npm ci
	@echo "→ Configura este comando en el Makefile según el stack del proyecto"

clean: ## Limpiar archivos temporales y caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml dist build
	@echo "Limpieza completada"

# ── Setup inicial ─────────────────────────────────────────────────────────────

setup: install infra-up ## Instalar dependencias y levantar infraestructura
	@echo ""
	@echo "✓ Setup completo. Iniciar servidor con: make dev"
