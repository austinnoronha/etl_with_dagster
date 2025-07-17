import sys

import pytest
from sqlalchemy import create_engine, text

sys.path.append('.')

from decimal import Decimal

from dagster import build_op_context

from jobs import fetch_data, store_data, validate_normalize


def test_fetch_data_returns_expected_count():
    context = build_op_context()
    data = fetch_data(context)
    assert isinstance(data, list)
    assert len(data) == 10  # Default FAKE_USER_COUNT
    for user in data:
        assert "id" in user and "name" in user and "email" in user
        assert "address" in user and "company" in user


def test_validate_normalize_converts_decimal():
    context = build_op_context()
    # Simulate a record with Decimal in nested field
    data = [
        {
            "id": 1,
            "name": "Test",
            "username": "testuser",
            "email": "test@example.com",
            "address": {"geo": {"lat": Decimal("1.23"), "lng": Decimal("4.56")}},
            "phone": "123",
            "website": "test.com",
            "company": {},
            "created_ts": None,
            "update_ts": None,
            "status": 1,
        }
    ]
    cleaned = validate_normalize(context, data)
    assert isinstance(cleaned[0]["address"]["geo"]["lat"], float)
    assert isinstance(cleaned[0]["address"]["geo"]["lng"], float)


@pytest.mark.integration
def test_store_data_integration():
    """
    Integration test for store_data. Tries to connect to the database using 'postgres' hostname (Docker Compose),
    and falls back to 'localhost' if not available (host testing). Skips if neither is available.
    """
    import datetime
    import uuid

    from dagster import build_op_context

    # Try both Docker Compose and host connection strings
    db_urls = [
        # os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/dagster"),
        "postgresql://postgres:postgres@localhost:5432/dagster"
    ]
    engine = None
    for db_url in db_urls:
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            engine = None
            continue
    if engine is None:
        pytest.skip("Database not available at 'postgres' or 'localhost'.")

    # Prepare test data
    test_id = str(uuid.uuid4())
    test_data = [
        {
            "id": test_id,
            "name": "Test User",
            "username": "testuser",
            "email": f"{test_id}@example.com",
            "address": {"geo": {"lat": 1.23, "lng": 4.56}},
            "phone": "123",
            "website": "test.com",
            "company": {"name": "TestCo"},
            "created_ts": datetime.datetime.now(datetime.UTC),
            "update_ts": datetime.datetime.now(datetime.UTC),
            "status": 1,
        }
    ]
    context = build_op_context()
    store_data(context, test_data)

    # Verify data was written
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": test_id}
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == test_id

    # Clean up
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": test_id})
