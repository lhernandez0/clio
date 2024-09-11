.PHONY: airflow-reqs

AIRFLOW_VERSION = 2.10.0
PYTHON_VERSION = 3.11

airflow-reqs: # Download airflow constraints
	curl -o airflow-constraints.txt https://raw.githubusercontent.com/apache/airflow/constraints-$(AIRFLOW_VERSION)/constraints-$(PYTHON_VERSION).txt

reqs: # Update requirements.txt
	venv/bin/pip-compile -o requirements.txt --upgrade requirements.in

dev: reqs # Run reqs and install dependencies
	venv/bin/pip install -r requirements.txt --no-cache-dir
	venv/bin/pre-commit install

VENV_PATH := $(shell venv/bin/python -c "import site; print(site.getsitepackages()[0])")
PLUGINS_PATH := $(shell pwd)/airflow/plugins
PTH_FILE := $(VENV_PATH)/airflow_plugins.pth

setup_plugins: # Add plugins path to site-packages
	@echo "Creating .pth file in site-packages directory..."
	@echo $(PLUGINS_PATH) > $(PTH_FILE)
	@echo ".pth file created at $(PTH_FILE)"

venv: # Create virtual environment
	`which python3` -m venv venv
	venv/bin/pip install -U pip pip-tools wheel --no-cache-dir
	setup_plugins

docker-build: # Build docker-compose services
	docker-compose build

docker-run: # Run docker-compose build up
	docker-compose up --build

db: # Set up PostgreSQL for Airflow in dev
	docker run --name airflow-postgres -e POSTGRES_USER=airflow -e POSTGRES_PASSWORD=airflow -e POSTGRES_DB=airflow -p 5432:5432 -d postgres:latest

test: # Run tests
	venv/bin/pytest -vv

help: # Show this help
	@awk 'BEGIN {FS = ":.*?# "} /^[a-zA-Z_-]+:.*?# .*$$/ {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
