import os

import pytest

from gino_admin import utils


@pytest.mark.parametrize("str_date", [""])
def test_extract_datetime_pattern(str_date):
    """
    "%B %d, %Y %I:%M %p",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%m-%d-%yT%H:%M:%S.%f",
    "%m-%d-%y %H:%M:%S",
    "%m-%d-%yT%H:%M:%S","""
    pass


def test_parse_db_uri():
    db_uri = "postgresql://test_u:test_p@test_url/test_db"
    utils.parse_db_uri(db_uri)
    assert os.environ.get("SANIC_DB_HOST") == "test_url"
    assert os.environ.get("SANIC_DB_USER") == "test_u"
    assert os.environ.get("SANIC_DB_PASSWORD") == "test_p"
    assert os.environ.get("SANIC_DB_DATABASE") == "test_db"
