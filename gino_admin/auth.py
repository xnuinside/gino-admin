import binascii
import os
from base64 import b64decode
from functools import wraps
from typing import Dict, Text, Tuple, Union

import asyncpg
from passlib.hash import pbkdf2_sha256
from sanic import response as r
from sanic_jwt import exceptions

from gino_admin import config
from gino_admin.history import log_history_event
from gino_admin.utils import logger

cfg = config.cfg


def token_validation():
    def decorator(route):
        @wraps(route)
        async def validate(request, *args, **kwargs):
            if not os.getenv("ADMIN_AUTH_DISABLE") == "1":
                if (
                    not request.cookies
                    or not request.cookies.get("auth-token")
                    or request.cookies.get("auth-token") not in cfg.sessions
                    or (
                        request.cookies["auth-token"] in cfg.sessions
                        and cfg.sessions[request.cookies["auth-token"]]["user_agent"]
                        != request.headers["User-Agent"]
                    )
                ):
                    return r.redirect(f"{cfg.route}/login")
                else:
                    request.ctx.session = {"_auth": True}
                    return await route(request, *args, **kwargs)
            else:
                request.ctx.session = {"_auth": True}
                return await route(request, *args, **kwargs)

        return validate

    return decorator


async def validate_login(request, _config):
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            message = "failed attempt to auth. no username provided"
            request.ctx.flash_messages.append(("error", message))
            request = log_history_event(request, message, "system: login")
            return False, request
        username = str(username)
        password = str(request.form.get("password"))
        base_user = cfg.app.config.get("ADMIN_USER")

        if username == base_user:
            if password == str(cfg.app.config.get("ADMIN_PASSWORD")):
                return username, request
            else:
                message = f"failed attempt to auth. wrong user: {username}"
                request.ctx.flash_messages.append(("error", message))
                request = log_history_event(request, message, "system: login")
                return False, request
        try:
            user_in_base = await cfg.admin_user_model.get(username)
            if not user_in_base:
                request.ctx.flash_messages.append(
                    (
                        "error",
                        f"There is no User with login <b>{username}</b>",
                    )
                )
                log_history_event(
                    request,
                    f"failed attempt to auth. wrong user: <b>{username}</b>",
                    "system: login",
                )
                return False, request
            if pbkdf2_sha256.verify(password, user_in_base.password_hash):
                return username, request
            log_history_event(
                request,
                f"failed attempt to auth. wrong password for user: <b>{username}</b>",
                "system: login",
            )
        except asyncpg.exceptions.UndefinedTableError:
            # mean table with users was not created yet
            request.ctx.flash_messages.append(
                (
                    "error",
                    f"<b>{username}</b> is not root user and table with gino admin users not exists yet",
                )
            )
    return False, request


def logout_user(request):
    if request.cookies["auth-token"] in cfg.sessions:
        del cfg.sessions[request.cookies["auth-token"]]
    request.cookies["auth-token"] = None
    return request


async def authenticate(request, *args, **kwargs):
    if not os.getenv("ADMIN_AUTH_DISABLE") == "1":
        if "Basic" in request.token:
            username, password = user_credentials_from_the_token(request.token)
        else:
            username, password = request.token.split(":")

        if not username or not password:
            raise exceptions.AuthenticationFailed("Missing username or password.")

        user_in_cfg = str(cfg.app.config["ADMIN_USER"])
        password_in_cfg = str(cfg.app.config["ADMIN_PASSWORD"])

        if username != user_in_cfg:
            raise exceptions.AuthenticationFailed("User not found.")

        if password != password_in_cfg:
            raise exceptions.AuthenticationFailed("Password is incorrect.")

        return {"user_id": 1, "username": username}
    else:
        return {"user_id": 1, "username": "admin_no_auth"}


def user_credentials_from_the_token(token: Union[Text, bytes]) -> Union[Dict, Tuple]:
    """ decode base64 token to get pass and user_id """

    if not token:
        return {"error": "Need to provide Basic token"}

    token = token.split("Basic ")

    if len(token) == 2:
        decoded_token = token[1]
    else:
        return {
            "error": "Invalid data in Basic token. Token must starts with 'Basic ' "
        }
    try:
        decoded_token = b64decode(decoded_token).decode("utf-8")
    except (UnicodeDecodeError, binascii.Error) as e:
        return {
            "error": "Invalid data in Basic token. Codec can't decode bytes. Error message:"
            f"{e.args}"
        }

    if ":" not in decoded_token:
        return {
            "error": "Invalid data in Basic token, token str before encoding must follow format user:password"
            f"You sent: {decoded_token}"
        }

    first_semicolon = decoded_token.index(":")
    user_id = decoded_token[:first_semicolon]
    password = decoded_token[(first_semicolon + 1) :]  # noqa E203
    logger.debug(f"User decoded from Basic token: '{user_id}'")
    return user_id, password
