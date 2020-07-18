import base_tests as b
import pytest
import tests_helpers as h


@pytest.fixture(scope="module")
def composite_app_url(module_scoped_container_getter):
    """ Wait for the api from fastapi_main_app_main to become responsive """
    return h.get_app_url(module_scoped_container_getter, "composite_csv")


@pytest.fixture(scope="module")
def admin_auth_headers(composite_app_url):
    """ get auth token """
    return h.get_auth_headers(composite_app_url)


@pytest.fixture(scope="module")
def initdb(composite_app_url, admin_auth_headers):
    """ run api call with auth token """
    return h.init_db(composite_app_url, admin_auth_headers, "composite_preset")


def test_main_service_run(composite_app_url):
    b.test_main_service_run(composite_app_url)


def test_admin_service_drop(admin_auth_headers, composite_app_url):
    b.test_admin_service_drop(admin_auth_headers, composite_app_url)


def test_presets_was_loaded(initdb):
    b.test_presets_was_loaded(initdb)
