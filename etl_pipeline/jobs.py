"""
File: jobs.py
Documentation: Defines the ETL pipeline Dagster job and its ops: fetch, validate_normalize, and store.
"""

from typing import Any, Dict, List

from dagster import OpExecutionContext, RetryPolicy, job, op

# Constants
DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(max_retries=3, delay=2)


@op(retry_policy=DEFAULT_RETRY_POLICY)
def fetch_data(context: OpExecutionContext) -> List[Dict[str, Any]]:
    """
    Fetch data from a vendor API or source.
    Returns a list of records (dictionaries).
    """
    data: List[Dict[str, Any]] = []
    # TODO: Implement actual fetch logic
    context.log.info("Fetching data from vendor...")
    return data


@op
def validate_normalize(
    context: OpExecutionContext, data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validate and normalize the fetched data.
    Returns a list of cleaned records.
    """
    cleaned_data: List[Dict[str, Any]] = (
        data  # TODO: Implement validation/normalization
    )
    context.log.info(f"Validating and normalizing {len(data)} records...")
    return cleaned_data


@op
def store_data(context: OpExecutionContext, cleaned_data: List[Dict[str, Any]]) -> None:
    """
    Store the cleaned data into the database.
    """
    context.log.info(f"Storing {len(cleaned_data)} records to DB...")
    # TODO: Implement DB storage logic
    pass


@job
def etl_job() -> None:
    """
    Dagster job that runs the ETL pipeline: fetch -> validate_normalize -> store.
    """
    store_data(validate_normalize(fetch_data()))
