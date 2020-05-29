import pytest
import requests


@pytest.fixture(scope="module")
def admin_auth_headers(base_app_url):
    """ get auth token """
    headers = {"Authorization": "admin:1234"}
    result = requests.post(f"{base_app_url}/admin/api/auth/", headers=headers)
    token = result.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture(scope="module")
def initdb(base_app_url, admin_auth_headers):
    """ run api call with auth token """
    result = requests.post(
        f"{base_app_url}/admin/api/presets/",
        json={"preset_id": "first_preset", "drop": True},
        headers=admin_auth_headers,
    )
    assert result.status_code == 200
    return True


def test_main_service_run(base_app_url):
    result = requests.get(base_app_url)
    assert result.status_code == 200


def test_admin_service_drop(admin_auth_headers, base_app_url):
    result = requests.post(
        f"{base_app_url}/admin/api/drop_db", headers=admin_auth_headers
    )
    assert result.status_code == 200


def test_presets_was_loaded(initdb):
    assert initdb
