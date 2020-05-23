import pytest
import requests


@pytest.fixture(scope="module")
def ui_session(base_app_url):
    """ run api call with auth token """
    session = requests.Session()
    result = session.post(
        f"{base_app_url}/admin/login", data={"username": "admin", "password": "1234"}
    )
    assert result.status_code == 200
    return session


def test_login_form(base_app_url):
    result = requests.post(f"{base_app_url}/admin/login")
    response = result.text
    assert result.status_code == 200
    assert "<html>" in response
    assert "<h2>Please sign in, you can try:</h2>" in response
    assert 'placeholder="password" type="password" value=""><br><br>' in response
    assert (
        """<input class="field username" id="name" name="username"
    placeholder="username" type="text" value=""><br><br>"""
        in response
    )
    assert (
        '<input id="submit"  class="ui button primary" name="submit" type="submit" value="Sign In">'
        in response
    )


def test_presets_page(base_app_url, ui_session):
    result = ui_session.get(f"{base_app_url}/admin/presets")
    response = result.text
    assert result.status_code == 200
    assert '<div class="ui three cards">' in response
    assert '<div class="header">First Preset</div>' in response
    assert '<div class="header">Second preset</div>' in response
    assert (
        """<button id="with_db" class="ui red inverted button"
                  name="with_db" value="with_db" type="submit">Load with DB Drop</button>"""
        in response
    )
    assert (
        '<button id="simple" class="ui green button" type="submit">Load Preset</button>'
        in response
    )
    assert '<form action="/admin/presets" method="post">' in response
