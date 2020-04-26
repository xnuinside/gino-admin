import os
from datetime import datetime
from typing import Callable, List

import asyncpg
from gino.ext.sanic import Gino
from jinja2 import FileSystemLoader
from sanic import Blueprint, Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin.auth import auth, validate_login
from gino_admin.utils import hash_method, reverse_hash_names, serialize_dict

loader = FileSystemLoader(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)

jinja = SanicJinja2(loader=loader)


class App:
    """ class to store links to main app data app.config and DB"""

    config = {}
    db = None


class Config:
    """ Gino Admin Panel settings """

    URL_PREFIX = "/admin"
    hash_method = hash_method
    models = {}
    session = {}
    app = App


cfg = Config

admin = Blueprint("admin", url_prefix=cfg.URL_PREFIX)


def exatract_date(date_str):

    date_object = datetime.strptime(date_str, "%m-%d-%y")
    return date_object


def exatract_time(datetime_str):

    datetime_object = datetime.strptime(datetime_str, "%m-%d-%y %H:%M:%S")
    return datetime_object


def extract_columns_data(model: Gino.Model):

    _hash = "_hash"
    types_map = {
        "INTEGER": int,
        "BIGINT": int,
        "VARCHAR": str,
        "FLOAT": float,
        "DECIMAL": float,
        "NUMERIC": float,
        "DATETIME": datetime,
        "DATE": datetime,
        "BOOLEAN": bool,
    }
    column_names = {}
    hashed_indexes = []
    for num, column in enumerate(cfg.app.db.tables[model].columns):
        if _hash in column.name:
            column_names[column.name.split(_hash)[0]] = {
                "type": "HASH",
                "nullable": column.nullable,
            }
            hashed_indexes.append(num)
        else:
            db_type = str(column.type).split("(")[0]
            column_names[column.name] = {
                "type": types_map.get(db_type, str),
                "nullable": column.nullable,
            }
    return column_names, hashed_indexes


@admin.middleware("request")
async def add_session(request):
    request["session"] = cfg.session


@admin.route("/")
@auth.login_required
@jinja.template("index.html")  # decorator method is staticmethod
async def bp_root(request):
    return jinja.render(
        "index.html",
        request,
        greetings="Hello, sanic!",
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model>", methods=["GET"])
@auth.login_required
async def admin_model(request, model):
    columns_data, hashed_indexes = extract_columns_data(model)
    model = cfg.app.db.tables[model]
    query = cfg.app.db.select([model])
    rows = await query.gino.all()
    columns_names = list(columns_data.keys())
    response = jinja.render(
        "model_view.html",
        request,
        model=model.name,
        columns=columns_names,
        model_data=rows,
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
    )
    return response


@admin.route("/<model>/add", methods=["GET"])
@auth.login_required
async def admin_model_add(request, model):
    columns_data, hashed_indexes = extract_columns_data(model)
    columns_names = list(columns_data.keys())

    response = jinja.render(
        "add_form.html",
        request,
        model=model,
        add=True,
        columns_names=columns_names,
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
    )
    return response


@admin.route("/<model>/add", methods=["POST"])
@auth.login_required
async def admin_model_add_submit(request, model):
    columns_data, hashed_indexes = extract_columns_data(model)
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False
    ]
    columns_names = list(columns_data.keys())
    request_params = {key: request.form[key][0] for key in request.form}
    not_filled = [x for x in required if x not in request_params]
    if not_filled:
        request["flash"](f"Fields {not_filled} required. Please fill it", "error")
    else:
        if hashed_indexes:
            request_params = reverse_hash_names(
                hashed_indexes, columns_names, request_params
            )
        try:
            for param in request_params:
                if "_hash" not in param and not isinstance(
                    request_params[param], columns_data[param]["type"]
                ):
                    if columns_data[param] is not datetime:
                        request_params[param] = columns_data[param]["type"](
                            request_params[param]
                        )
                    else:
                        # todo for date
                        request_params[param] = exatract_time(request_params[param])
            await cfg.models[model].create(**request_params)
            request["flash"]("Object was added", "success")
        except ValueError as e:
            request["flash"](e.args, "error")
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            request["flash"](e.args, "error")
        except asyncpg.exceptions.UniqueViolationError:
            request["flash"](
                f"{model.capitalize()} with such id already exists", "error"
            )
        except asyncpg.exceptions.NotNullViolationError as e:
            column = e.args[0].split("column")[1].split("violates")[0]
            request["flash"](f"Field {column} cannot be null", "error")

    return jinja.render(
        "add_form.html",
        request,
        model=model,
        objects=cfg.app.db.tables,
        obj=None,
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/<obj_id>/edit", methods=["GET"])
@auth.login_required
async def admin_model_edit(request, model_id, obj_id):
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.models[model_id]
    obj = serialize_dict((await model.get(obj_id)).to_dict())
    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        obj=obj,
        objects=cfg.app.db.tables,
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/<obj_id>/edit", methods=["POST"])
@auth.login_required
async def admin_model_edit_post(request, model_id, obj_id):
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.models[model_id]
    obj = await model.get(obj_id)
    request_params = {key: request.form[key][0] for key in request.form}
    if hashed_indexes:
        request_params = reverse_hash_names(
            hashed_indexes, columns_names, request_params
        )
    try:
        await obj.update(**request_params).apply()
        obj = obj.to_dict()
    except asyncpg.exceptions.UniqueViolationError:
        request["flash"](
            f"{model_id.capitalize()} with such id already exists", "error"
        )
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request["flash"](f"Field {column} cannot be null", "error")
    return jinja.render(
        "add_form.html",
        request,
        model=model_id,
        obj=obj,
        objects=cfg.app.db.tables,
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
        url=f"{cfg.URL_PREFIX}/{model}/{obj_id}/edit",
    )


@admin.route("/logout")
@auth.login_required
async def logout(request):
    auth.logout_user(request)
    return response.redirect("login")


def handle_no_auth(request):
    return response.json(dict(message="unauthorized"), status=401)


@admin.route("/<model>/delete", methods=["POST"])
@auth.login_required
async def admin_model_delete(request, model):
    """ route for delete item per row """
    request_params = {key: request.form[key][0] for key in request.form}
    await cfg.models[model].delete.where(
        cfg.models[model].id == request_params["id"]
    ).gino.status()
    request["flash"](f"Object with {request_params['id']} was deleted", "success")
    return response.redirect(f"/admin/{model}")


@admin.route("/<model>/delete_all", methods=["POST"])
@auth.login_required
async def admin_model_delete_all(request, model):
    try:
        await cfg.models[model].delete.where(True).gino.status()
        request["flash"]("Object was added", "success")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return response.redirect(f"/admin/{model}")


@admin.route("/<model>/<tag>", methods=["POST"])
@auth.login_required
async def admin_model_update(request, model, tag):
    # TODO
    ...


@admin.route("/login", methods=["GET", "POST"])
async def login(request):
    _login = validate_login(request, cfg.app.config)
    if _login:
        return response.redirect("/")
    else:
        request["flash"]("Password or login is incorrect", "error")
    return jinja.render(
        "login.html", request, objects=cfg.app.db.tables, url_prefix=cfg.URL_PREFIX,
    )


@admin.middleware("response")
async def halt_response(request, response):
    # catch response and send data for menu
    return response


def add_admin_panel(
    app: Sanic, db: Gino, gino_models: List, custom_hash_method: Callable = None
):
    """ init admin panel and configure """
    cfg.models = {model.__tablename__: model for model in gino_models}
    cfg.app.db = db
    app.blueprint(admin)
    if custom_hash_method:
        cfg.hash_method = custom_hash_method
    try:
        app.config.AUTH_LOGIN_ENDPOINT = "admin.login"
        auth.setup(app)
    except RuntimeError:
        pass
    jinja.init_app(app)
    cfg.app.config = app.config
