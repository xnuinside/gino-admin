import datetime
import os

import asyncpg
import sanic

from gino_admin import config

cfg = config.cfg


def add_history_model(db):
    if "gino_admin_history" not in db.tables:

        class History(db.Model):

            __tablename__ = cfg.history_table_name

            id = db.Column(
                db.String(), db.Sequence("history"), unique=True, primary_key=True
            )
            datetime = db.Column(db.DateTime())
            user = db.Column(db.String())
            route = db.Column(db.String())
            log_message = db.Column(db.String())
            object_id = db.Column(db.String())

        cfg.history_model = History
        cfg.history_data_columns = [
            column.name
            for num, column in enumerate(db.tables[cfg.history_table_name].columns)
        ]


async def write_history_after_response(request: sanic.request.Request):
    if not os.getenv("ADMIN_AUTH_DISABLE") == "1":
        if (
            not request.cookies
            or not request.cookies.get("auth-token")
            or request.cookies["auth-token"] not in cfg.sessions
        ):
            return
        else:
            user = cfg.sessions[request.cookies["auth-token"]]["user"]

    else:
        user = "AUTH_DISABLED"
    history_row = {
        "user": user,
        "route": request.endpoint.split(".")[-1],
        "log_message": request["history_action"]["log_message"],
        "object_id": str(request["history_action"]["object_id"]),
        "datetime": datetime.datetime.now(),
    }
    try:
        await cfg.history_model.create(**history_row)
    except asyncpg.exceptions.UndefinedTableError:
        await cfg.app.db.gino.create_all()
        await cfg.history_model.create(**history_row)
