import datetime
import pytest
from gino_admin import utils


@pytest.mark.parametrize('str_date', [''])
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
    