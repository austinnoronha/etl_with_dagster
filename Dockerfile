# Documentation: Dockerfile for ETL Dagster Service using Poetry
# Uses Python 3.12, Poetry for dependency management, and exposes Dagster CLI

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Install Poetry
RUN pip install --upgrade pip \
    && pip install poetry

WORKDIR /app

# Copy only dependency files first for better Docker cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev dependencies for production)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy the rest of the project
COPY . /app

EXPOSE 3000

CMD ["dagster", "dev", "-h", "0.0.0.0"]
