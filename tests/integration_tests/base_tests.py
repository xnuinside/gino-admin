import requests


def test_main_service_run(app_url):
    result = requests.get(app_url)
    assert result.status_code == 200


def test_admin_service_drop(auth_headers, app_url):
    result = requests.post(f"{app_url}/admin/api/init_db", headers=auth_headers)
    assert result.status_code == 200


def test_presets_was_loaded(initdb):
    assert initdb
