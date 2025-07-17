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
docker-compose up -d
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

3. Make It Configurable
- You can use Docker Compose profiles or environment variables to switch between local (default) and Postgres-backed storage.
- For example, you could have two dagster.yaml files and mount the one you want, or use a template and environment variables.

4. Example Directory Structure
``text
etl_with_dagster/
  dagster_home/
    dagster.yaml
  docker-compose.yml
  ...
```

5. Summary Table
| Storage Type	| How to Enable	| Robustness	| Notes |
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