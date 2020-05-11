import os
from functools import wraps

from sanic import response as r

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
