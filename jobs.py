"""
File: jobs.py
Documentation: Defines the ETL pipeline Dagster job, its ops, and a schedule to run the job every hour. Now uses Faker to generate user data instead of fetching from an external API.
"""

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List

from dagster import (
    Definitions,
    OpExecutionContext,
    RetryPolicy,
    ScheduleDefinition,
    job,
    op,
)
from faker import Faker
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError

# Constants
DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(max_retries=3, delay=2)
REQUIRED_FIELDS: List[str] = ["id", "name", "email"]
FAKE_USER_COUNT: int = 10


def convert_decimal(obj):
    """
    Recursively convert Decimal objects to float in dicts/lists for JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


@op(retry_policy=DEFAULT_RETRY_POLICY)
def fetch_data(context: OpExecutionContext) -> List[Dict[str, Any]]:
    """
    Generate fake user data using the Faker library, including created_ts, update_ts, and status fields.
    Uses UUID for id. Ensures id and email are unique.
    """
    fake: Faker = Faker()
    data: List[Dict[str, Any]] = []
    now = datetime.now(UTC)
    for _ in range(FAKE_USER_COUNT):
        user: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "name": fake.name(),
            "username": fake.user_name(),
            "email": fake.unique.email(),
            "address": {
                "street": fake.street_name(),
                "suite": fake.secondary_address(),
                "city": fake.city(),
                "zipcode": fake.zipcode(),
                "geo": {
                    "lat": fake.latitude(),
                    "lng": fake.longitude(),
                },
            },
            "phone": fake.phone_number(),
            "website": fake.domain_name(),
            "company": {
                "name": fake.company(),
                "catchPhrase": fake.catch_phrase(),
                "bs": fake.bs(),
            },
            "created_ts": now,
            "update_ts": now,
            "status": 1,
        }
        context.log.info(
            f"FAKER: id={user['id']}, name={user['name']}, username={user['username']}, email={user['email']}"
        )
        data.append(user)
    context.log.info(f"Generated {len(data)} fake user records.")
    return data


@op
def validate_normalize(
    context: OpExecutionContext, data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validate and normalize the fetched data.
    Returns a list of cleaned records. Converts Decimal to float for JSON columns.
    """
    cleaned_data: List[Dict[str, Any]] = []
    for record in data:
        valid: bool = True
        for field in REQUIRED_FIELDS:
            if field not in record or not record[field]:
                context.log.warning(
                    f"Record missing required field '{field}': {record}"
                )
                valid = False
        if valid:
            # Example normalization: trim strings
            normalized = {
                k: (v.strip() if isinstance(v, str) else v) for k, v in record.items()
            }
            cleaned_data.append(normalized)
    # Convert Decimal to float for all records (for JSON serialization)
    cleaned_data = [convert_decimal(record) for record in cleaned_data]
    context.log.info(
        f"Validated and normalized {len(cleaned_data)} of {len(data)} records."
    )
    return cleaned_data


def get_engine() -> Engine:
    """
    Create a SQLAlchemy engine using DATABASE_URL from environment.
    """
    db_url: str = os.getenv(
        "DATABASE_URL", "postgresql://etl_user:etl_pass@postgres:5432/etl_db"
    )
    return create_engine(db_url)


@op
def store_data(context: OpExecutionContext, cleaned_data: List[Dict[str, Any]]) -> None:
    """
    Store the cleaned data into the database using SQLAlchemy.
    Uses upsert (on_conflict_do_update) to update existing records with new Faker data each run.
    Uniqueness is enforced on id (primary key). Email remains unique.
    """
    if not cleaned_data:
        context.log.warning("No data to store.")
        return
    engine: Engine = get_engine()
    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String),
        Column("username", String),
        Column("email", String, unique=True),
        Column("address", JSON),
        Column("phone", String),
        Column("website", String),
        Column("company", JSON),
        Column("created_ts", DateTime),
        Column("update_ts", DateTime),
        Column("status", Integer, default=1),
        extend_existing=True,
    )
    try:
        metadata.create_all(engine)
        with engine.begin() as conn:
            for record in cleaned_data:
                insert_stmt = (
                    insert(users)
                    .values(
                        id=record["id"],
                        name=record["name"],
                        username=record["username"],
                        email=record["email"],
                        address=record["address"],
                        phone=record["phone"],
                        website=record["website"],
                        company=record["company"],
                        created_ts=record["created_ts"],
                        update_ts=record["update_ts"],
                        status=record["status"],
                    )
                    .on_conflict_do_update(
                        index_elements=['id'],
                        set_={
                            "name": record["name"],
                            "username": record["username"],
                            "email": record["email"],
                            "address": record["address"],
                            "phone": record["phone"],
                            "website": record["website"],
                            "company": record["company"],
                            "update_ts": record["update_ts"],
                            "status": record["status"],
                        },
                    )
                )
                conn.execute(insert_stmt)
        context.log.info(f"Stored {len(cleaned_data)} records to DB.")
    except SQLAlchemyError as e:
        context.log.error(f"DB error: {e}")
        raise


@job
def etl_job() -> None:
    """
    Dagster job that runs the ETL pipeline: fetch -> validate_normalize -> store.
    """
    store_data(validate_normalize(fetch_data()))


# Schedule: Run etl_job every hour
etl_schedule = ScheduleDefinition(
    job=etl_job,
    cron_schedule="0 * * * *",  # every hour
    execution_timezone="UTC",
    name="etl_hourly_schedule",
)

defs = Definitions(
    jobs=[etl_job],
    schedules=[etl_schedule],
)
