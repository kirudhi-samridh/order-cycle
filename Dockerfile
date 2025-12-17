FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps if needed (psycopg binary wheels avoid libpq)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy repo
COPY . /app

# Make shared package importable
ENV PYTHONPATH=/app:/app/packages/common

# Command is provided per-service in docker-compose.yml


