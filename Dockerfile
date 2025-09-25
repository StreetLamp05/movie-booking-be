# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Poetry 1.8.3
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

ENV PATH="$POETRY_HOME/bin:$PATH"
WORKDIR /app

# Copy lock files
COPY pyproject.toml poetry.lock ./

# Install deps
RUN poetry install --no-root

# Copy source & entrypoint
COPY src ./src
COPY tests ./tests
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000
ENV FLASK_APP=src.app:create_app
