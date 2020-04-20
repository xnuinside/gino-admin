from typing import List, Callable
import os
import asyncpg

from sanic_jinja2 import SanicJinja2
from sanic import Blueprint, Sanic, response

from gino.ext.sanic import Gino
from gino_admin.auth import auth, validate_login

from passlib.hash import pbkdf2_sha256

from jinja2 import FileSystemLoader

loader = FileSystemLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

jinja = SanicJinja2(loader=loader)

models = {}
config = {}
app_db = None

url_prefix = "/admin"

admin = Blueprint("admin", url_prefix=url_prefix)


session = {}

hash_method = pbkdf2_sha256.hash


def extract_column_names(model: Gino.Model):

    _hash = '_hash'

    column_names = []
    hashed_indexes = []
    for num, column in enumerate(app_db.tables[model].columns):
        if _hash in column.name:
            column_names.append(column.name.split(_hash)[0])
            hashed_indexes.append(num)
        else:
            column_names.append(column.name)
    return column_names, hashed_indexes



@admin.middleware("request")
async def add_session(request):
    request["session"] = session


@admin.route("/")
@auth.login_required
@jinja.template("index.html")  # decorator method is staticmethod
async def bp_root(request):
    return jinja.render(
        "index.html",
        request,
        greetings="Hello, sanic!",
        objects=app_db.tables,
        url_prefix=url_prefix,
    )


@admin.route("/<model>", methods=["GET"])
@auth.login_required
async def admin_model(request, model):
    columns_names, hashed_indexes = extract_column_names(model)
    model = app_db.tables[model]
    query = app_db.select([model])
    rows = await query.gino.all()

    response = jinja.render(
        "model_view.html",
        request,
        model=model.name,
        columns=columns_names,
        model_data=rows,
        objects=app_db.tables,
        url_prefix=url_prefix,
    )
    return response


@admin.route("/<model>/add", methods=["GET"])
@auth.login_required
async def admin_model_add(request, model):
    columns_names, hashed_indexes = extract_column_names(model)
    response = jinja.render(
        "add_form.html",
        request,
        model=model,
        columns_names=columns_names,
        objects=app_db.tables,
        url_prefix=url_prefix,
    )
    return response


@admin.route("/<model>/add", methods=["POST"])
@auth.login_required
async def admin_model_add_submit(request, model):
    columns_names, hashed_indexes = extract_column_names(model)
    request_params = {key: request.form[key][0] for key in request.form}
    if hashed_indexes:
        for hashed_index in hashed_indexes:
            request_params[columns_names[hashed_index]+'_hash'] = hash_method(
                request_params[columns_names[hashed_index]])
            del request_params[columns_names[hashed_index]]
    try:
        await models[model].create(**request_params)
        request["flash"]("Object was added", "success")
    except asyncpg.exceptions.UniqueViolationError:
        request["flash"]("User with such id already exists", "error")
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request["flash"](f"Field {column} cannot be null", "error")

    return jinja.render(
        "add_form.html",
        request,
        model=model,
        objects=app_db.tables,
        columns_names=columns_names,
        url_prefix=url_prefix,
    )


@admin.route("/<model>/upload", methods=["POST"])
@auth.login_required
async def admin_model_edit(request, model):
    columns_names = [x.name for x in app_db.tables[model].columns]
    request_params = {key: request.form[key][0] for key in request.form}
    try:
        await models[model].create(**request_params)
        request["flash"]("Object was added", "success")
    except asyncpg.exceptions.UniqueViolationError:
        request["flash"]("User with such id already exists", "error")
    except asyncpg.exceptions.NotNullViolationError as e:
        column = e.args[0].split("column")[1].split("violates")[0]
        request["flash"](f"Field {column} cannot be null", "error")

    return jinja.render(
        "add_form.html",
        request,
        model=model,
        objects=app_db.tables,
        columns_names=columns_names,
        url_prefix=url_prefix,
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
    columns_names = [x.name for x in app_db.tables[model].columns]
    request_params = {key: request.form[key][0] for key in request.form}
    # TODO: not all objects can have id
    await models[model].delete.where(
        models[model].id == request_params["action_id"]
    ).gino.status()
    request["flash"]("Object was added", "success")
    return jinja.render(
        "model_view.html",
        request,
        model=model,
        objects=app_db.tables,
        columns_names=columns_names,
        url_prefix=url_prefix,
    )


@admin.route("/<model>/delete_all", methods=["POST"])
@auth.login_required
async def admin_model_delete_all(request, model):
    columns_names = [x.name for x in app_db.tables[model].columns]
    await models[model].delete.where(True).gino.status()
    request["flash"]("Object was added", "success")
    return jinja.render(
        "model_view.html",
        request,
        model=model,
        objects=app_db.tables,
        columns_names=columns_names,
        url_prefix=url_prefix,
    )


@admin.route("/<model>/<tag>", methods=["POST"])
@auth.login_required
async def admin_model_update(request, model, tag):
    # TODO
    ...


@admin.route("/login", methods=["GET", "POST"])
async def login(request):
    _login = validate_login(request, config)
    if _login:
        return response.redirect("/")
    else:
        request["flash"]("Password or login is incorrect", "error")
    return jinja.render(
        "login.html",
        request,
        objects=app_db.tables,
        url_prefix=url_prefix,
    )


@admin.middleware("response")
async def halt_response(request, response):
    # catch response and send data for menu
    return response


def add_admin_panel(app: Sanic, db: Gino, gino_models: List, custom_hash_method: Callable = None):
    # todo need to change this to object params
    global app_db, models, config, hash_method
    models = {model.__tablename__: model for model in gino_models}
    app_db = db
    app.blueprint(admin)
    if custom_hash_method:
        hash_method = custom_hash_method
    try:
        app.config.AUTH_LOGIN_ENDPOINT = "admin.login"
        auth.setup(app)
    except RuntimeError:
        pass
    jinja.init_app(app)
    config = app.config
