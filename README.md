# ETL with Dagster

## Description
A robust, observable ETL pipeline built with Dagster, Python, and Postgres. This project demonstrates best practices for data engineering, including retries, normalization, validation, and automated scheduling. Designed for learning and as a template for production ETL workflows.

## Use Case
- Learn how to build a modern ETL pipeline using Dagster and Python
- See how to fetch, validate, normalize, and store data from a vendor API to a database
- Explore observability, error handling, and scheduling in a real-world setup

## Technologies & Minimum Requirements
- **Python**: >=3.12, <=3.13.3
- **Dagster**: 1.11+
- **PostgreSQL**: 16 (via Docker)
- **SQLAlchemy**: 2.0+
- **Poetry**: for dependency management
- **Docker & Docker Compose**: for local orchestration
- **psycopg2-binary**: for Postgres connectivity

## Poetry Setup
1. Install Poetry: https://python-poetry.org/docs/#installation
2. Install dependencies:
   ```sh
   poetry install
   ```
3. (Optional) Add new dependencies:
   ```sh
   poetry add <package>
   ```

## Dockerfile & Docker Compose
- The Dockerfile uses Poetry to install only main dependencies for production.
- Docker Compose sets up both the ETL service and a Postgres database, with persistent volumes for data and Dagster logs.

## Commands

### Start Dagster Locally (for development)
```sh
poetry run dagster dev
```

### Build and Start with Docker Compose
```sh
docker-compose build
docker-compose up
```
- Access Dagster UI: [http://localhost:3000](http://localhost:3000)
- Postgres is available on port 5432 (user: `etl_user`, pass: `etl_pass`, db: `etl_db`)

## Notes & Troubleshooting
- **Python Version**: Ensure your Python version is >=3.12 and <=3.13.3 due to Dagster webserver constraints.
- **Missing psycopg2**: If you see `ModuleNotFoundError: No module named 'psycopg2'`, add `psycopg2-binary` to your dependencies.
- **Dagster Job Discovery**: If you see `No [tool.dagster] block in pyproject.toml found`, add:
  ```toml
  [tool.dagster]
  module_name = "jobs"
  ```
- **Docker Compose Version Warning**: The `version:` key in `docker-compose.yml` is obsolete and can be removed.
- **CLI Not Found in Docker**: If `dagster` is not found, ensure Poetry installs dependencies globally (`poetry config virtualenvs.create false`) or add the venv's bin to `PATH`.
- **Database Table Creation**: The ETL pipeline auto-creates the `users` table in Postgres if it does not exist.
- **Scheduling**: The ETL job is scheduled to run every hour automatically via Dagster's scheduler.
- **Volumes**: Postgres data and Dagster logs are persisted using Docker volumes (`pgdata`, `dagster_logs`).

## License
MIT or your preferred license.
