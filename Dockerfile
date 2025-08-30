# 👉 Dockerfile for Media RAG Project
FROM python:3.12-slim

######################################################################
# System dependencies
######################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

######################################################################
# Working directory
######################################################################
WORKDIR /app

######################################################################
# Install Python dependencies
# Copy only Pipfile first → better build cache reuse
######################################################################
COPY Pipfile Pipfile.lock ./
RUN pip install --no-cache-dir pipenv && \
    pipenv install --deploy --ignore-pipfile --system

######################################################################
# Copy project files
######################################################################
COPY Data/documents-with-ids.json Data/documents-with-ids.json
COPY assistant .

######################################################################
# Ports and runtime
######################################################################
EXPOSE 5000

# NOTE: Gunicorn is production-grade; Uvicorn is lighter for dev
# Default Gunicorn timeout = 30s → increase due to LLM latency
# Workers: tune based on CPU (e.g., 2–4 for small servers)
# CMD gunicorn --bind 0.0.0.0:5000 --timeout 400 app:app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "1200", "app:app"]

######################################################################
# END OF FILE
######################################################################
