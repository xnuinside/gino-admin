import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@pytest.fixture(scope="module")
def main_app_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))

    service = module_scoped_container_getter.get("fastapi_main_app_main").network_info[
        0
    ]
    api_url = f"http://{service.hostname}:{service.host_port}"
    return api_url


@pytest.fixture(scope="module")
def admin_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_admin to become responsive """
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))

    service = module_scoped_container_getter.get("fastapi_main_app_admin").network_info[
        0
    ]
    api_url = f"http://{service.hostname}:{service.host_port}/admin"
    return api_url


@pytest.fixture(scope="module")
def admin_auth_headers(admin_url):
    """ get auth token """
    headers = {"Authorization": "admin:1234"}
    result = requests.post(f"{admin_url}/api/auth/", headers=headers)
    token = result.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture(scope="module")
def initdb(admin_url, admin_auth_headers):
    """ run api call with auth token """
    result = requests.post(
        f"{admin_url}/api/presets/",
        json={"preset_id": "preset_1", "drop": True},
        headers=admin_auth_headers,
    )
    assert result.status_code == 200


def test_main_service_run(main_app_url):
    result = requests.get(main_app_url)
    assert result.status_code == 200


def test_admin_service_run(admin_url):
    result = requests.get(admin_url)
    assert result.status_code == 200


def test_main_service_users(main_app_url, initdb):
    """ run test that depend on data in DB """
    result = requests.get(f"{main_app_url}/users").json()
    assert result
    assert result == {"count_users": 5}


def test_admin_service_drop(admin_auth_headers, admin_url):
    result = requests.post(f"{admin_url}/api/init_db", headers=admin_auth_headers)
    assert result.status_code == 200
