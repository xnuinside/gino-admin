from io import StringIO

import requests


def test_main_service_run(app_url):
    result = requests.get(app_url)
    assert result.status_code == 200


def test_admin_service_drop(auth_headers, app_url):
    result = requests.post(f"{app_url}/admin/api/init_db", headers=auth_headers)
    assert result.status_code == 200


def test_presets_was_loaded(initdb):
    assert initdb


def test_upload_csv_file(auth_headers, app_url):
    test_csv_file = (
        "address,phone,email,name,password,id\n"
        "969 Loopy road,(011) 999-9699,cuckoo@mailbox.com,Yosseffer,53gsr4,baboon\n"
        "55 Shady ave,(222) 240-654234,yowza@yahoo.com,Karl,553dda,zonker\n"
    )
    values = {"model_id": "users"}
    result = requests.post(
        f"{app_url}/admin/api/upload_csv",
        files={"upload_file": ("users.csv", StringIO(test_csv_file), "text/csv")},
        params=values,
        headers=auth_headers,
    )
    assert result.status_code == 200
