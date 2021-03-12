import datetime
import os
from typing import Text

import asyncpg
import sanic
from sanic import request

from gino_admin import config

cfg = config.cfg


def add_history_model(db) -> None:
    if cfg.history_table_name not in db.tables:

        class GinoAdminHistory(db.Model):

            __tablename__ = cfg.history_table_name

            id = db.Column(
                db.String(),
                db.Sequence("gino_admin_seq_history"),
                unique=True,
                primary_key=True,
            )
            datetime = db.Column(db.DateTime())
            user = db.Column(db.String())
            route = db.Column(db.String())
            log_message = db.Column(db.String())
            object_id = db.Column(db.String())

        schema = db.schema + "." if db.schema else ""
        cfg.history_table_name = schema + cfg.history_table_name
        cfg.history_model = GinoAdminHistory
        cfg.history_data_columns = [
            column.name for column in db.tables[cfg.history_table_name].columns
        ]


async def write_history_after_response(request: sanic.request.Request) -> None:
    if not os.getenv("ADMIN_AUTH_DISABLE") == "1":
        if (
            not request.cookies
            or not request.cookies.get("auth-token")
            or request.cookies["auth-token"] not in cfg.sessions
        ):
            user = "no_auth"
        else:
            user = cfg.sessions[request.cookies["auth-token"]]["user"]

    else:
        user = "AUTH_DISABLED"
    route = request.url.split("admin/")[1]
    history_row = {
        "user": user,
        "route": route,
        "log_message": request.ctx.history_action.get("log_message", ""),
        "object_id": str(request.ctx.history_action.get("object_id", "none")),
        "datetime": datetime.datetime.now(),
    }
    try:
        await cfg.history_model.create(**history_row)
    except asyncpg.exceptions.UndefinedTableError:
        await cfg.app.db.gino.create_all()
        await cfg.history_model.create(**history_row)


def log_history_event(request: request.Request, message: Text, object_id: Text) -> None:
    request.ctx.history_action["log_message"] = message
    request.ctx.history_action["object_id"] = object_id
    return request
