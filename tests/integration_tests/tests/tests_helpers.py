import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_app_url(module_scoped_container_getter, service_name):
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))

    service = module_scoped_container_getter.get(service_name).network_info[0]
    api_url = f"http://{service.hostname}:{service.host_port}"
    return api_url


def get_auth_headers(app_url):
    headers = {"Authorization": "admin:1234"}
    result = requests.post(f"{app_url}/admin/api/auth/", headers=headers)
    token = result.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def init_db(app_url, auth_headers, preset_name):
    result = requests.post(
        f"{app_url}/admin/api/presets/",
        json={"preset_id": preset_name, "drop": True},
        headers=auth_headers,
    )
    assert result.status_code == 200
    return True
