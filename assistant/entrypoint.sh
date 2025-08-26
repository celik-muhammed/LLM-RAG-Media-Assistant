#!/bin/bash
set -e

# Wait for Postgres
until pg_isready -h postgres -p 5432 -U user; do
  echo "Waiting for Postgres..."
  sleep 2
done

echo "Postgres ready, running db prep"
python db_prep.py

# Start app
# timeout must be higher than slow requests (LLM calls).
# Default Gunicorn timeout is 30 seconds. --timeout 120 sets 2 minutes.
# If your /question route waits for Ollama (or model loading) longer than that → worker gets killed.
# exec uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4 --timeout 120
exec gunicorn app:app --bind 0.0.0.0:5000 --timeout 120
