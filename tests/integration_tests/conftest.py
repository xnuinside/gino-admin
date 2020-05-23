import os

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

pytest_plugins = ["docker_compose"]


@pytest.fixture(scope="module")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "test-docker-compose.yml")


@pytest.fixture(scope="module")
def base_app_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
    request_session.mount("http://", HTTPAdapter(max_retries=retries))

    service = module_scoped_container_getter.get("base_app").network_info[0]
    api_url = f"http://{service.hostname}:{service.host_port}"
    return api_url
