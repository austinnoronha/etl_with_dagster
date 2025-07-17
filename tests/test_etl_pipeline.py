"""
File: test_etl_pipeline.py
Documentation: Unit tests for the ETL pipeline ops using pytest.
"""

from dagster import build_op_context

from etl_pipeline.jobs import fetch_data


def test_fetch_data_returns_list() -> None:
    """
    Test that fetch_data returns a list.
    """
    context = build_op_context()
    result = fetch_data(context)
    assert isinstance(result, list)
