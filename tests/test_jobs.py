import sys

sys.path.append('.')

from decimal import Decimal

from dagster import build_op_context

from jobs import fetch_data, validate_normalize


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
