"""
File: jobs.py
Documentation: Defines the ETL pipeline Dagster job, its ops, and a schedule to run the job every hour.
"""

import os
from typing import Any, Dict, List

import requests
from dagster import (
    Definitions,
    OpExecutionContext,
    RetryPolicy,
    ScheduleDefinition,
    job,
    op,
)
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError

# Constants
DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(max_retries=3, delay=2)
VENDOR_API_URL: str = "https://jsonplaceholder.typicode.com/users"  # Example public API
REQUIRED_FIELDS: List[str] = ["id", "name", "email"]


@op(retry_policy=DEFAULT_RETRY_POLICY)
def fetch_data(context: OpExecutionContext) -> List[Dict[str, Any]]:
    """
    Fetch data from a vendor API.
    Returns a list of records (dictionaries).
    """
    try:
        context.log.info(f"Fetching data from vendor API: {VENDOR_API_URL}")
        response = requests.get(VENDOR_API_URL, timeout=10)
        response.raise_for_status()
        data: List[Dict[str, Any]] = response.json()
        context.log.info(f"Fetched {len(data)} records.")
        return data
    except Exception as e:
        context.log.error(f"Error fetching data: {e}")
        raise


@op
def validate_normalize(
    context: OpExecutionContext, data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validate and normalize the fetched data.
    Returns a list of cleaned records.
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
    context.log.info(
        f"Validated and normalized {len(cleaned_data)} of {len(data)} records."
    )
    return cleaned_data


def get_engine() -> Engine:
    """
    Create a SQLAlchemy engine using DATABASE_URL from environment.
    """
    db_url: str = os.getenv(
        "DATABASE_URL", "postgresql://etl_user:etl_pass@localhost:5432/etl_db"
    )
    return create_engine(db_url)


@op
def store_data(context: OpExecutionContext, cleaned_data: List[Dict[str, Any]]) -> None:
    """
    Store the cleaned data into the database using SQLAlchemy.
    """
    if not cleaned_data:
        context.log.warning("No data to store.")
        return
    engine: Engine = get_engine()
    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("email", String),
        extend_existing=True,
    )
    try:
        metadata.create_all(engine)
        with engine.begin() as conn:
            for record in cleaned_data:
                insert_stmt = users.insert().values(
                    id=record["id"], name=record["name"], email=record["email"]
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
