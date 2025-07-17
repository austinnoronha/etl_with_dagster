# ETL with Dagster

## Description
A robust, observable ETL pipeline built with Dagster, Python, and Postgres. This project demonstrates best practices for data engineering, including retries, normalization, validation, and automated scheduling. Designed for learning and as a template for production ETL workflows.

## Why Use PostgreSQL for Dagster Metadata and ETL Data?

- **Kubernetes & Cloud-Native Deployments:** In cloud or containerized environments (like Kubernetes), local disk storage is ephemeral and not reliable for metadata or job history. Using a database ensures all Dagster state (run history, schedules, logs) and ETL data are persistent and robust.
- **Scalability:** PostgreSQL is production-grade, supports concurrent access, and is well-supported by Dagster and SQLAlchemy.
- **Disaster Recovery:** Database backups are easier to manage and restore than local files or Docker volumes.
- **Multi-Service Access:** Multiple services (e.g., analytics, BI tools) can access the same data store.

## Use Case
- **Production-Ready ETL:** This project is designed for real-world, production ETL pipelines where reliability, observability, and persistence are critical.
- **Learning Modern Data Engineering:** Demonstrates best practices for using Dagster with a robust database backend, including upserts, schema management, and container orchestration.
- **Cloud-Native Deployments:** Ready for Kubernetes or any orchestrator where persistent local storage is not guaranteed.

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
docker-compose up -d
```
- Access Dagster UI: [http://localhost:3000](http://localhost:3000)
- Postgres is available on port 5432 (user: `etl_user`, pass: `etl_pass`, db: `etl_db`)

### Start Everything (Docker Compose)
```sh
docker-compose up --build -d
```
- Brings up Dagster and Postgres with correct networking and persistent volumes.

### View Dagster UI
- Open [http://localhost:3000](http://localhost:3000) in your browser.

### Run All Tests (Host)
```sh
pytest
```

### Run Integration Tests with Localhost DB (Host)
```sh
# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dagster"; pytest -m integration
# Linux/macOS
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dagster" pytest -m integration
```

### Run Tests Inside the Dagster Container (Docker Compose)
```sh
docker-compose exec dagster pytest
```

### Remove All Docker Volumes (reset DB and Dagster state)
```sh
docker-compose down -v
```

### Troubleshooting: Connection Issues
- If you see `could not translate host name "postgres" to address: No such host is known`, you are running on your host and need to use `localhost` as the DB hostname.
- If you see `connection refused`, ensure Postgres is running and port 5432 is exposed.
- To clear any environment variable that may interfere:
  - **Windows PowerShell:** `Remove-Item Env:DATABASE_URL`
  - **Linux/macOS:** `unset DATABASE_URL`

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
- **Volumes**: Postgres data and Dagster logs are persisted using Docker volumes (`pgdata`, `dagster_logs`, `dagster_home`).

## License
MIT or your preferred license.

## Notes:
## 1. In Dagster, when you define a schedule, it is not enabled by default for safety reasons. This is why you see the radio button in the UI and have to manually enable it the first time.

Why is this the case?
- Dagster wants to prevent accidental automatic runs when you first deploy or develop.
- This gives you a chance to review, test, and confirm before jobs start running on a schedule.

How to Enable the Schedule Automatically
- There is currently no built-in way to auto-enable schedules on first launch via code or config.
- You must enable each schedule once via the Dagster UI (or via the Dagster GraphQL API/CLI).

But:
- Once enabled, the schedule will remain enabled across restarts (as long as Dagster's storage is persistent).
- If you clear Dagster's storage (e.g., delete the SQLite file or Docker volume), you will need to re-enable the schedule.

Summary
- Manual enablement is required the first time (by design).
- After enabling, it stays enabled (unless Dagster storage is wiped).
- No code/config-only way to auto-enable on first run (as of Dagster 1.11).

## 2. Upsert (Insert or Update)
Instead of a plain insert, use an "upsert" (insert or update on conflict). In SQLAlchemy, you can use `on_conflict_do_update` or `on_conflict_do_nothing` for Postgres.

Example: Use `on_conflict_do_nothing`
This will skip inserting a row if the primary key already exists.

```bash
from sqlalchemy.dialects.postgresql import insert

# ... inside store_data ...
for record in cleaned_data:
    insert_stmt = insert(users).values(
        id=record["id"],
        name=record["name"],
        email=record["email"]
    ).on_conflict_do_nothing(index_elements=['id'])
    conn.execute(insert_stmt)
```

Or Truncate Table Before Insert (for demo/testing)
If you want to always replace the data (for learning/testing), you can clear the table before inserting:
`conn.execute(users.delete())`
Add this before your insert loop.

Which Should You Use?
- Upsert: Use this for production-like behavior (no duplicates, keeps existing data).
- Truncate: Use this for learning/testing if you want a fresh table each run.

## 3. How to Make Dagster State Persistent
Set the `DAGSTER_HOME` Environment Variable
Dagster will use the directory specified by DAGSTER_HOME for all persistent storage (logs, run history, schedules, etc.).
You should:
Create a directory (e.g., `/app/dagster_home`) in your container.
Mount a Docker volume to this directory for persistence.

Update Your docker-compose.yml
Add a volume for Dagster home and set the environment variable:
```bash
services:
  etl:
    # ... other config ...
    environment:
      - DATABASE_URL=postgresql://etl_user:etl_pass@db:5432/etl_db
      - DAGSTER_HOME=/app/dagster_home
    volumes:
      - .:/app
      - dagster_home:/app/dagster_home
      - dagster_logs:/app/dagster_logs  # (optional, for separate logs)
    # ... rest of config ...

volumes:
  pgdata:
  dagster_home:   # <-- new persistent volume for Dagster state
  dagster_logs:
```

(Optional) Use a Database for Dagster Storage

For even more robust persistence (especially for production), you can configure Dagster to use Postgres for its run storage, event log storage, and schedule storage.

This requires more configuration in your dagster.yaml (which should live in DAGSTER_HOME).

## 4. Dagster perstitance data storeage with Postgres 
You can configure Dagster to use Postgres for its internal storage (run history, event logs, schedules, etc.) for production-grade robustness. This is done by providing a dagster.yaml configuration file in your `DAGSTER_HOME` directory and setting the appropriate environment variables in your `docker-compose.yml`.

1. Create a `dagster.yaml` in `dagster_home`
This file tells Dagster to use Postgres for all its internal storage:

```bash
# dagster_home/dagster.yaml
run_storage:
  module: dagster_postgres.run_storage
  class: PostgresRunStorage
  config:
    postgres_db:
      username: etl_user
      password: etl_pass
      hostname: db
      db_name: etl_db
      port: 5432

event_log_storage:
  module: dagster_postgres.event_log_storage
  class: PostgresEventLogStorage
  config:
    postgres_db:
      username: etl_user
      password: etl_pass
      hostname: db
      db_name: etl_db
      port: 5432

schedule_storage:
  module: dagster_postgres.schedule_storage
  class: PostgresScheduleStorage
  config:
    postgres_db:
      username: etl_user
      password: etl_pass
      hostname: db
      db_name: etl_db
      port: 5432

# Optional: asset and daemon storage
# asset_storage:
#   module: dagster_postgres.asset_storage
#   class: PostgresAssetStorage
#   config:
#     postgres_db:
#       username: etl_user
#       password: etl_pass
#       hostname: db
#       db_name: etl_db
#       port: 5432

# daemon_storage:
#   module: dagster_postgres.daemon_storage
#   class: PostgresDaemonStorage
#   config:
#     postgres_db:
#       username: etl_user
#       password: etl_pass
#       hostname: db
#       db_name: etl_db
#       port: 5432
```

2. Update docker-compose.yml
- Ensure `dagster.yaml` is present in your `dagster_home` directory (on your host).
- Mount `./dagster_home:/app/dagster_home` as you already do.
- Add the required Dagster Postgres package to your dependencies:
  ```bash
  poetry add dagster-postgres
  ```
  (and rebuild your Docker image)

  You might have to remove the volumes you created earlier
  ```bash
  docker volume rm etl_with_dagster_pgdata
  docker volume rm pgdata
  ```

3. Make It Configurable
- You can use Docker Compose profiles or environment variables to switch between local (default) and Postgres-backed storage.
- For example, you could have two dagster.yaml files and mount the one you want, or use a template and environment variables.

4. Example Directory Structure
```text
etl_with_dagster/
  dagster_home/
    dagster.yaml
  docker-compose.yml
  ...
```

5. Summary Table
   
| Storage Type	| How to Enable | Robustness | Notes |
| -------- | ------- | ------- | ------- |
| Default (local)	| No dagster.yaml	| Low	| Volumes only |
| Postgres (recommended)	| dagster.yaml as above	| High	| Survives  everything |

6. Next Steps
- Add `dagster-postgres` to your dependencies.
- Create `dagster_home/dagster.yaml` as above.
- Restart your stack.

Summary of Steps
- Add the convert_decimal function to your code.
- Use it to process each record in validate_normalize before returning.

---

## Dagster UI - Job Overview

![Dagster Job Overview](media/dagster_ui_jobs_job_overview.png)
![Dagster Job Overview](media/dagster_ui_jobs_list.png)

## Dagster UI - Run History

![Dagster Run History](media/dagster_ui_runs_queue.png)
![Dagster Run History](media/dagster_ui_runs_job_info.png)

## Postgres Users Table

![Postgres Users Table](media/pg_sql_users_table.png)


## Dagster UI - Job Automation

![Dagster Job Overview](media/dagster_ui_automation_list.png)
![Dagster Job Overview](media/dagster_ui_automation_job_overview.png)

## Database Connection for Local and Docker Compose

- The ETL pipeline and tests use the `DATABASE_URL` environment variable to connect to Postgres.
- When running in Docker Compose, `DATABASE_URL` is set to use the `postgres` hostname (the Docker service name).
- When running tests on your local machine, the test will try both `postgres` and `localhost` as the database hostname, so you can run tests outside Docker as long as the Postgres port is exposed.

### Example connection strings
- Docker Compose: `postgresql://postgres:postgres@postgres:5432/dagster`
- Localhost: `postgresql://postgres:postgres@localhost:5432/dagster`

## Running Integration Tests

- The integration test for `store_data` will auto-detect the correct database hostname.
- If neither `postgres` nor `localhost` is available, the test will be skipped.
- To run all tests:
  ```sh
  pytest
  ```
- To run only integration tests:
  ```sh
  # Windows
  $env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dagster"; pytest
  # to only run integrations
  $env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dagster"; pytest -m integration
  or 
  # Linux
  DATABASE_URL="postgresql://postgres:postgres@localhost:5432/dagster" pytest
  ```
- To run clean env values:
  ```sh
  # Windows
  Remove-Item Env:DATABASE_URL  
  or 
  # Linux
  unset DATABASE_URL  
  ```

## Previous Release

- See the [v1.0.0 release on GitHub](https://github.com/austinnoronha/etl_with_dagster/releases/tag/1.0.0) for the initial version of this project.
- **Highlights of v1.0.0:**
  - Robust, observable ETL pipeline built with Dagster, Python, and Postgres
  - Demonstrates best practices: retries, normalization, validation, automated scheduling
  - All Dagster jobs, schedules, and configurations were stored as files in the `dagster_home` folder
  - Foundation for moving Dagster metadata to Postgres for efficiency and scalability
