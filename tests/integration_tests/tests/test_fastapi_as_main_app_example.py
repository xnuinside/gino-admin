import base_tests as b
import pytest
import requests
import tests_helpers as h


@pytest.fixture(scope="module")
def main_app_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    return h.get_app_url(module_scoped_container_getter, "fastapi_main_app_main")


@pytest.fixture(scope="module")
def admin_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    return h.get_app_url(module_scoped_container_getter, "fastapi_main_app_admin")


@pytest.fixture(scope="module")
def admin_auth_headers(admin_url):
    """ get auth token """
    return h.get_auth_headers(admin_url)


@pytest.fixture(scope="module")
def initdb(admin_url, admin_auth_headers):
    """ run api call with auth token """
    return h.init_db(admin_url, admin_auth_headers, "preset_1")


def test_main_service_run(main_app_url):
    b.test_main_service_run(main_app_url)


def test_admin_service_run(admin_url):
    b.test_main_service_run(admin_url)


def test_presets_was_loaded(initdb):
    b.test_presets_was_loaded(initdb)


def test_main_service_users(main_app_url, initdb):
    """ run test that depend on data in DB """
    result = requests.get(f"{main_app_url}/users").json()
    assert result
    assert result == {"count_users": 5}


def test_admin_service_drop(admin_auth_headers, admin_url):
    b.test_admin_service_drop(admin_auth_headers, admin_url)
