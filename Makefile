.PHONY: help install test run clean setup

help:
	@echo "ERPNext CRM Integration - Available Commands"
	@echo "=============================================="
	@echo "make install       - Install dependencies from requirements.txt"
	@echo "make test          - Run all tests with coverage"
	@echo "make test-fast     - Run tests without coverage"
	@echo "make run           - Start the Flask development server"
	@echo "make clean         - Remove Python cache and build artifacts"
	@echo "make setup         - Set up development environment (install + venv notes)"
	@echo "make lint          - Check code quality (if black/flake8 installed)"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

test-fast:
	pytest tests/ -v

run:
	python -m flask --app app.main run --debug

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf build dist *.egg-info

setup: install
	@echo "✓ Dependencies installed"
	@echo "✓ Development environment ready"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and fill in your ERPNext credentials"
	@echo "2. Run 'make run' to start the development server"
	@echo "3. Run 'make test' to verify everything works"
