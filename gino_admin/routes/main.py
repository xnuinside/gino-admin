import os
import uuid
from ast import literal_eval
from datetime import datetime
from random import randint
from typing import Text

import asyncpg
from sanic import response
from sanic.request import Request

from gino_admin import auth, utils
from gino_admin.core import admin, jinja
from gino_admin.routes.logic import (drop_and_recreate_all_tables,
                                     insert_data_from_csv, render_model_view)
from gino_admin.utils import cfg, extract_columns_data


@admin.route("/")
@auth.token_validation()
@jinja.template("index.html")  # decorator method is staticmethod
async def bp_root(request):
    return jinja.render(
        "index.html", request, objects=cfg.models, url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/logout")
@auth.token_validation()
async def logout(request: Request):
    auth.logout_user(request)
    return response.redirect("login")


@admin.route("/login", methods=["GET", "POST"])
async def login(request):
    _login = auth.validate_login(request, cfg.app.config)
    if _login:
        _token = utils.generate_token(request.ip)
        cfg.sessions[_token] = request.headers["User-Agent"]
        request.cookies["auth-token"] = _token
        request["session"] = {"_auth": True}
        _response = jinja.render(
            "index.html", request, objects=cfg.models, url_prefix=cfg.URL_PREFIX
        )
        _response.cookies["auth-token"] = _token
        return _response
    else:
        request["flash"]("Password or login is incorrect", "error")
    return jinja.render(
        "login.html", request, objects=cfg.models, url_prefix=cfg.URL_PREFIX,
    )


def handle_no_auth(request: Request):
    return response.json(dict(message="unauthorized"), status=401)


@admin.route("/<model_id>/deepcopy", methods=["POST"])
@auth.token_validation()
async def model_deepcopy(request, model_id):
    # TODO:
    ...


@admin.route("/<model_id>/copy", methods=["POST"])
@auth.token_validation()
async def model_copy(request, model_id):
    """ route for copy item per row """
    request_params = {key: request.form[key][0] for key in request.form}
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    request_params["id"] = columns_data["id"]["type"](request_params["id"])
    model = cfg.models[model_id]
    # id can be str or int
    if isinstance(request_params["id"], str):
        new_obj_id = request_params["id"] + "_copy_" + uuid.uuid1().hex[5:10]
    else:
        new_obj_id = request_params["id"] + randint(0, 10000000000)
    bas_obj = (await model.get(request_params["id"])).to_dict()
    bas_obj["id"] = new_obj_id
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False
    ]
    for item in required:
        # todo: need to document this behaviour in copy step
        if (item in bas_obj and not bas_obj[item]) or item not in bas_obj:
            bas_obj[item] = bas_obj["id"]
            if columns_data[item]["type"] == "HASH":
                bas_obj[item] = cfg.hash_method(bas_obj["id"])

    bas_obj = utils.reverse_hash_names(hashed_indexes, columns_names, bas_obj)
    try:
        await model.create(**bas_obj)
        request["flash"](
            f"Object with {request_params['id']} was copied with id {bas_obj['id']}",
            "success",
        )
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return await render_model_view(request, model_id)


@admin.route("/db_drop", methods=["GET"])
@auth.token_validation()
async def db_drop_view(request: Request):
    data = {}
    for model_id, model in cfg.models.items():
        data[model_id] = await cfg.app.db.func.count(model.id).gino.scalar()
    return jinja.render(
        "db_drop.html",
        request,
        data=data,
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/db_drop", methods=["POST"])
@auth.token_validation()
async def db_drop_run(request: Request):

    data = literal_eval(request.form["data"][0])
    count = 0
    for _, value in data.items():
        count += value
    await drop_and_recreate_all_tables()

    data = {}
    for model_id, model in cfg.models.items():
        data[model_id] = await cfg.app.db.func.count(model.id).gino.scalar()
    request["flash"](f"{count} object was deleted", "success")
    return jinja.render(
        "db_drop.html",
        request,
        data=data,
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/presets", methods=["GET"])
@auth.token_validation()
async def presets_view(request: Request):
    return jinja.render(
        "presets.html",
        request,
        presets=utils.get_presets(),
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/presets/", methods=["POST"])
@auth.token_validation()
async def presets_use(request: Request):
    preset = literal_eval(request.form["preset"][0])
    if "with_db" in request.form:
        await drop_and_recreate_all_tables()
        request["flash"](f"DB was successful Dropped", "success")
    try:
        for model_id, file_path in preset["files"].items():
            request, code = await insert_data_from_csv(
                os.path.join(cfg.presets_folder, file_path), model_id.lower(), request
            )
        request["flash"](f"Preset {preset['name']} was loaded", "success")
    except FileNotFoundError:
        request["flash"](f"Wrong file path in Preset {preset['name']}.", "error")
    return jinja.render(
        "presets.html",
        request,
        presets=utils.get_presets(),
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/upload/", methods=["POST"])
@auth.token_validation()
async def file_upload(request: Request, model_id: Text):
    if not os.path.exists(cfg.upload_dir):
        os.makedirs(cfg.upload_dir)
    upload_file = request.files.get("file_names")
    if not upload_file:
        request["flash"]("No file chosen to Upload", "error")
        return response.redirect(f"/admin/{model_id}")
    file_name = utils.secure_filename(upload_file.name)
    if not utils.valid_file_size(upload_file.body, cfg.max_file_size):
        return response.redirect("/?error=invalid_file_size")
    else:
        file_path = f"{cfg.upload_dir}/{file_name}_{datetime.now().isoformat()}.{upload_file.type.split('/')[1]}"
        await utils.write_file(file_path, upload_file.body)
        request, code = await insert_data_from_csv(file_path, model_id, request)
        return await render_model_view(request, model_id)


@admin.route("/sql_run", methods=["GET"])
@auth.token_validation()
async def sql_query_run_view(request):
    return jinja.render(
        "sql_runner.html", request, objects=cfg.models, url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/sql_run", methods=["POST"])
@auth.token_validation()
async def sql_query_run(request):
    result = []
    if not request.form.get("sql_query"):
        request["flash"](f"SQL query cannot be empty", "error")
    else:
        sql_query = request.form["sql_query"][0]
        try:
            result = await cfg.app.db.status(cfg.app.db.text(sql_query))
        except asyncpg.exceptions.PostgresSyntaxError as e:
            request["flash"](f"{e.args}", "error")
    return jinja.render(
        "sql_runner.html",
        request,
        columns=result[1],
        result=result[1],
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )
