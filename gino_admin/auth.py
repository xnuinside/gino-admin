import os
from functools import wraps

from sanic import response as r
from sanic_jwt import exceptions

from gino_admin.utils import cfg


def token_validation():
    def decorator(route):
        @wraps(route)
        async def validate(request, *args, **kwargs):
            if not os.getenv("ADMIN_AUTH_DISABLE") == "1":
                if (
                    not request.cookies
                    or request.cookies["auth-token"] not in cfg.sessions
                    or (
                        request.cookies["auth-token"] in cfg.sessions
                        and cfg.sessions[request.cookies["auth-token"]]
                        != request.headers["User-Agent"]
                    )
                ):
                    return r.redirect("/admin/login")
                else:
                    request["session"] = {"_auth": True}
                    return await route(request, *args, **kwargs)
            else:
                return await route(request, *args, **kwargs)

        return validate

    return decorator


def validate_login(request, config):
    if request.method == "POST":
        username = str(request.form.get("username"))
        password = str(request.form.get("password"))
        admin_user = str(config["ADMIN_USER"])
        admin_password = str(config["ADMIN_PASSWORD"])
        if username == admin_user and password == admin_password:
            return True
    return False


def logout_user(request):
    if request.cookies["auth-token"] in cfg.sessions:
        del cfg.sessions[request.cookies["auth-token"]]
    request.cookies["auth-token"] = None
    return request


class AdminUser:
    # todo: switch custom auth to JWT and users store in DB
    def __init__(self, _id, username, password):
        self.id = _id
        self.username = username
        self.password = password

    def __repr__(self):
        return "User(id='{}')".format(self.id)

    def to_dict(self):
        return {"user_id": self.id, "username": self.username}


def init_users():
    users = [
        AdminUser(1, cfg.app.config["ADMIN_USER"], cfg.app.config["ADMIN_PASSWORD"])
    ]
    return users


async def authenticate(request, *args, **kwargs):
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    users = init_users()

    username_table = {u.username: u for u in users}

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    user = username_table.get(username, None)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if password != user.password:
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user
