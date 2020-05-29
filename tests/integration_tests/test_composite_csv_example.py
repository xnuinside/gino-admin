import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@pytest.fixture(scope="module")
def composite_app_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))

    service = module_scoped_container_getter.get("composite_csv").network_info[0]
    api_url = f"http://{service.hostname}:{service.host_port}"
    return api_url


@pytest.fixture(scope="module")
def admin_auth_headers(composite_app_url):
    """ get auth token """
    headers = {"Authorization": "admin:1234"}
    result = requests.post(f"{composite_app_url}/admin/api/auth/", headers=headers)
    token = result.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture(scope="module")
def initdb(composite_app_url, admin_auth_headers):
    """ run api call with auth token """
    result = requests.post(
        f"{composite_app_url}/admin/api/presets/",
        json={"preset_id": "composite_preset", "drop": True},
        headers=admin_auth_headers,
    )
    assert result.status_code == 200
    return True


def test_main_service_run(composite_app_url):
    result = requests.get(composite_app_url)
    assert result.status_code == 200


def test_admin_service_drop(admin_auth_headers, composite_app_url):
    result = requests.post(
        f"{composite_app_url}/admin/api/drop_db", headers=admin_auth_headers
    )
    assert result.status_code == 200


def test_presets_was_loaded(initdb):
    assert initdb
