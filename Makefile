# 👉 Makefile for Media RAG Project
# Provides common development, testing, and deployment commands

.PHONY: help clean install deps venv venv-system docker-up docker-down cli streamlit \
        env-setup env-clean ollama-models ollama-ping ollama-models-docker ollama-ping-docker \
        api-question api-feedback test

######################################################################
# VARIABLES
######################################################################

PYTHON        ?= python
DOCKER        ?= docker compose
OLLAMA_HOST   ?= http://localhost:11434/v1
OLLAMA_MODEL  ?= phi3
API_HOST      ?= http://localhost:5000

######################################################################
# GENERAL
######################################################################

help:
	@echo "Available commands:"
	@echo "  make deps             - Install project dependencies"
	@echo "  make venv             - Create a local virtual environment with Pipenv"
	@echo "  make venv-system      - Install Pipenv dependencies system-wide"
	@echo "  make clean            - Remove cache, virtual env, artifacts"
	@echo "  make docker-up        - Start services with Docker Compose"
	@echo "  make docker-down      - Stop services"
	@echo "  make cli              - Run CLI chat client"
	@echo "  make streamlit        - Run Streamlit chat app"
	@echo "  make test             - Run tests with pytest"
	@echo "  make env-setup        - Initialize environment variables (.envrc)"
	@echo "  make env-clean        - Remove .envrc and reset direnv"
	@echo "  make ollama-*         - Check Ollama LLM service"
	@echo "  make api-*            - Test API endpoints"

clean:
	@echo "Cleaning project..."
	rm -rf __pycache__ .pytest_cache .mypy_cache .venv
	@echo "Done."

######################################################################
# DEPENDENCIES
######################################################################

deps:
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install -r requirements.txt -r requirements_dev.txt
	@echo "Dependencies installed."

venv:
	@echo "Creating Pipenv virtual environment..."
	$(PYTHON) -m pipenv install --ignore-pipfile --deploy
	@echo "Virtual environment created."

venv-system:
	@echo "Installing Pipenv environment system-wide..."
	$(PYTHON) -m pipenv install --ignore-pipfile --deploy --system
	@echo "System-wide environment installed."

######################################################################
# DOCKER
######################################################################

docker-up:
	@echo "Starting services with Docker Compose..."
	$(DOCKER) up

docker-down:
	@echo "Stopping services..."
	$(DOCKER) down

######################################################################
# APPLICATION
######################################################################

cli:
	@echo "Starting CLI Chat..."
	$(PYTHON) cli.py

streamlit:
	@echo "Starting Streamlit Chat..."
	$(PYTHON) st_app.py

test:
	@echo "Running tests..."
	pytest -v

######################################################################
# ENVIRONMENT
######################################################################

env-setup:
	@echo "Setting up environment variables..."
	cp .envrc_template .envrc
	direnv allow
	@echo "Environment ready."

env-clean:
	@echo "Cleaning environment variables..."
	rm -f .envrc
	direnv deny || true
	@echo "Environment cleaned."

######################################################################
# OLLAMA (LLM API) - default port 11434
######################################################################

ollama-models:
	curl -f $(OLLAMA_HOST)/models

ollama-ping:
	curl $(OLLAMA_HOST)/chat/completions \
		-H "Content-Type: application/json" \
		-d '{ "model": "$(OLLAMA_MODEL)", "messages": [{"role":"user","content":"ping"}] }'

ollama-models-docker:
	curl -f http://ollama:11434/v1/models

ollama-ping-docker:
	curl http://ollama:11434/v1/chat/completions \
		-H "Content-Type: application/json" \
		-d '{ "model": "$(OLLAMA_MODEL)", "messages": [{"role":"user","content":"ping"}] }'

######################################################################
# FLASK API - default port 5000
######################################################################

api-question:
	curl -X POST $(API_HOST)/question \
		-H "Content-Type: application/json" \
		-d '{"question": "How do I report copyright infringement?"}'

api-feedback:
	curl -X POST $(API_HOST)/feedback \
		-H "Content-Type: application/json" \
		-d '{"question": "ping", "answer": "ping", "relevance": "RELEVANT"}'

######################################################################
# END OF FILE
######################################################################
