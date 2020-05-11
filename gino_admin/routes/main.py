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
from gino_admin.routes.crud import model_view_table
from gino_admin.routes.logic import (count_elements_in_db,
                                     drop_and_recreate_all_tables,
                                     insert_data_from_csv)
from gino_admin.utils import cfg


@admin.route("/")
@auth.token_validation()
@jinja.template("index.html")  # decorator method is staticmethod
async def bp_root(request):
    return jinja.render(
        "index.html", request, objects=cfg.models, url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/logout", methods=["GET"])
async def logout(request: Request):
    request = auth.logout_user(request)
    return jinja.render(
        "login.html", request, objects=cfg.models, url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/logout", methods=["POST"])
async def logout_post(request: Request):
    return await login(request)


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


@admin.route("/<model_id>/deepcopy", methods=["POST"])
@auth.token_validation()
async def model_deepcopy(request, model_id):
    # TODO:
    ...


@admin.route("/<model_id>/copy", methods=["POST"])
@auth.token_validation()
async def model_copy(request, model_id):
    """ route for copy item per row """
    model_data = cfg.models[model_id]
    columns_data = model_data["columns_data"]
    request_params = {elem: request.form[elem][0] for elem in request.form}
    key = model_data["key"]
    request_params[key] = columns_data[key]["type"](request_params[key])
    model = cfg.models[model_id]["model"]
    # id can be str or int
    # todo: need fix for several unique columns
    if isinstance(request_params[key], str):
        new_obj_id = (
            request_params[key]
            + f"{'_' if not request_params[key].endswith('_') else ''}"
            + uuid.uuid1().hex[5:10]
        )
        len_ = model_data["columns_data"][key]["len"]
        if len_:
            if new_obj_id[:len_] == request_params[key]:
                # if we spend all id previous
                new_obj_id = new_obj_id[
                    len_ : len_ + len_  # noqa E203
                ]  # auto format from black
            else:
                new_obj_id = new_obj_id[:len_]
    else:
        # todo: need to check ints with max size
        new_obj_id = request_params[key] + randint(0, 10000000000)
    bas_obj = (await model.get(request_params[key])).to_dict()
    bas_obj[key] = new_obj_id
    for item in model_data["required_columns"]:
        # todo: need to document this behaviour in copy step
        if (item in bas_obj and not bas_obj[item]) or item not in bas_obj:
            bas_obj[item] = bas_obj[key]
            if columns_data[item]["type"] == "HASH":
                bas_obj[item] = cfg.hash_method(bas_obj[key])
    bas_obj = utils.reverse_hash_names(model_id, bas_obj)
    try:
        await model.create(**bas_obj)
        flash_message = (
            f"Object with {key} {request_params[key]} was copied with {key} {bas_obj[key]}",
            "success",
        )
    except asyncpg.exceptions.UniqueViolationError as e:
        flash_message = (
            f"Duplicate in Unique column Error during copy: {e.args}. \n"
            f"Try to rename existed id or add manual.",
            "error",
        )
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        flash_message = (e.args, "error")
    return await model_view_table(request, model_id, flash_message)


@admin.route("/db_drop", methods=["GET"])
@auth.token_validation()
async def db_drop_view(request: Request):
    return jinja.render(
        "db_drop.html",
        request,
        data=await count_elements_in_db(),
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

    request["flash"](f"{count} object was deleted", "success")
    return jinja.render(
        "db_drop.html",
        request,
        data=await count_elements_in_db(),
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/presets", methods=["GET"])
@auth.token_validation()
async def presets_view(request: Request):
    return jinja.render(
        "presets.html",
        request,
        presets_folder=cfg.presets_folder,
        presets=utils.get_presets(),
        objects=cfg.models,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/settings", methods=["GET"])
@auth.token_validation()
async def settings_view(request: Request):
    return jinja.render(
        "settings.html",
        request,
        settings=utils.get_settings(),
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


@admin.middleware("request")
async def print_on_request(request):
    request["flash_messages"] = []


@admin.route("/<model_id>/upload/", methods=["POST"])
@auth.token_validation()
async def file_upload(request: Request, model_id: Text):
    if not os.path.exists(cfg.upload_dir):
        os.makedirs(cfg.upload_dir)
    upload_file = request.files.get("file_names")
    if not upload_file:
        flash_message = ("No file chosen to Upload", "error")
        return await model_view_table(request, model_id, flash_message)
    file_name = utils.secure_filename(upload_file.name)
    if not utils.valid_file_size(upload_file.body, cfg.max_file_size):
        return response.redirect("/?error=invalid_file_size")
    else:
        file_path = f"{cfg.upload_dir}/{file_name}_{datetime.now().isoformat()}.{upload_file.type.split('/')[1]}"
        await utils.write_file(file_path, upload_file.body)
        request, code = await insert_data_from_csv(file_path, model_id, request)
        return await model_view_table(request, model_id, request["flash_messages"])


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
