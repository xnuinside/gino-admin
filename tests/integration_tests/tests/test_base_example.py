import base_tests as b
import pytest
import tests_helpers as h


@pytest.fixture(scope="module")
def base_app_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    return h.get_app_url(module_scoped_container_getter, "base_app")


@pytest.fixture(scope="module")
def admin_auth_headers(base_app_url):
    """ get auth token """
    return h.get_auth_headers(base_app_url)


@pytest.fixture(scope="module")
def initdb(base_app_url, admin_auth_headers):
    """ run api call with auth token """
    return h.init_db(base_app_url, admin_auth_headers, "first_preset")


def test_main_service_run(base_app_url):
    b.test_main_service_run(base_app_url)


def test_admin_service_drop(admin_auth_headers, base_app_url):
    b.test_admin_service_drop(admin_auth_headers, base_app_url)


def test_presets_was_loaded(initdb):
    b.test_presets_was_loaded(initdb)


def test_upload_csv_file(admin_auth_headers, base_app_url):
    b.test_upload_csv_file(admin_auth_headers, base_app_url)
