import os
from csv import reader
from datetime import datetime
from typing import Callable, List

import asyncpg
from gino.ext.sanic import Gino
from jinja2 import FileSystemLoader
from sanic import Blueprint, Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin import auth, utils
from gino_admin.utils import cfg, extract_columns_data

loader = FileSystemLoader(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)
jinja = SanicJinja2(loader=loader)

cfg.jinja = jinja
admin = Blueprint("admin", url_prefix=cfg.URL_PREFIX)


@admin.route("/")
@auth.token_validation()
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
@auth.token_validation()
async def admin_model(request, model):
    columns_data, hashed_indexes = extract_columns_data(model)
    columns_names = list(columns_data.keys())
    model = cfg.app.db.tables[model]
    query = cfg.app.db.select([model])
    rows = await query.gino.all()
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
@auth.token_validation()
async def admin_model_add(request, model):
    columns_data, hashed_indexes = extract_columns_data(model)
    columns_names = list(columns_data.keys())

    response = jinja.render(
        "add_form.html",
        request,
        model=model,
        add=True,
        obj={},
        columns_names=columns_names,
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
    )
    return response


@admin.route("/<model>/add", methods=["POST"])
@auth.token_validation()
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
            request_params = utils.reverse_hash_names(
                hashed_indexes, columns_names, request_params
            )
        try:
            request_params = utils.correct_types(request_params, columns_data)
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
        obj={},
        columns_names=columns_names,
        url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/<model_id>/<obj_id>/edit", methods=["GET"])
@auth.token_validation()
async def admin_model_edit(request, model_id, obj_id):
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.models[model_id]
    # id can be str or int
    obj_id = columns_data["id"]["type"](obj_id)
    obj = utils.serialize_dict((await model.get(obj_id)).to_dict())
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
@auth.token_validation()
async def admin_model_edit_post(request, model_id, obj_id):
    columns_data, hashed_indexes = extract_columns_data(model_id)
    columns_names = list(columns_data.keys())
    model = cfg.models[model_id]
    obj = await model.get(columns_data["id"]["type"](obj_id))
    request_params = {
        key: request.form[key][0] if request.form[key][0] != "None" else None
        for key in request.form
    }
    if hashed_indexes:
        request_params = utils.reverse_hash_names(
            hashed_indexes, columns_names, request_params
        )
    request_params = utils.correct_types(request_params, columns_data)
    if hashed_indexes:
        request_params = utils.reverse_hash_names(
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
        url=f"{cfg.URL_PREFIX}/{model_id}/{obj_id}/edit",
    )


@admin.route("/logout")
@auth.token_validation()
async def logout(request):
    auth.logout_user(request)
    return response.redirect("login")


def handle_no_auth(request):
    return response.json(dict(message="unauthorized"), status=401)


@admin.route("/<model_id>/delete", methods=["POST"])
@auth.token_validation()
async def admin_model_delete(request, model_id):
    """ route for delete item per row """
    request_params = {key: request.form[key][0] for key in request.form}
    columns_data, hashed_indexes = extract_columns_data(model_id)
    request_params["id"] = columns_data["id"]["type"](columns_data["id"])
    await cfg.models[model_id].delete.where(
        cfg.models[model_id].id == request_params["id"]
    ).gino.status()
    request["flash"](f"Object with {request_params['id']} was deleted", "success")
    return response.redirect(f"/admin/{model_id}")


@admin.route("/<model>/delete_all", methods=["POST"])
@auth.token_validation()
async def admin_model_delete_all(request, model):
    try:
        await cfg.models[model].delete.where(True).gino.status()
        request["flash"]("Object was added", "success")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return response.redirect(f"/admin/{model}")


@admin.route("/<model_id>/upload/", methods=["POST"])
@auth.token_validation()
async def file_upload(request, model_id):
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

        # open file in read mode
        with open(file_path, "r") as read_obj:
            # pass the file object to reader() to get the reader object
            csv_reader = reader(read_obj)
            # Iterate over each row in the csv using reader object
            header = None
            id_added = []
            try:
                errors = []
                for num, row in enumerate(csv_reader):
                    # row variable is a list that represents a row in csv
                    if num == 0:
                        columns_data, hashed_indexes = extract_columns_data(model_id)
                        columns_names = list(columns_data.keys())
                        header = [x.strip().replace("\ufeff", "") for x in row]
                        hashed_columns_names = [
                            columns_names[index] for index in hashed_indexes
                        ]
                        for _num, name in enumerate(header):
                            if name in hashed_columns_names:
                                header[_num] = name + "_hash"
                            if name not in columns_names:
                                request["flash"](
                                    f"Wrong columns in CSV file. Header did not much model's columns. "
                                    f"For {model_id.capitalize()} possible columns {columns_names}",
                                    "error",
                                )
                                return response.redirect(f"/admin/{model_id}/")
                    else:
                        row = {header[index]: value for index, value in enumerate(row)}
                        row = utils.correct_types(row, columns_data)
                        try:
                            await cfg.models[model_id].create(**row)
                        except Exception as e:
                            errors.append((num, row["id"], e.args))
                            continue
                        id_added.append(row["id"])
                        print(errors)
                if errors:
                    request["flash"](
                        f"Errors: was not added  (row number, row id, error) : {errors}",
                        "error",
                    )
                request["flash"](f"Objects with ids {id_added} was added", "success")
            except ValueError as e:
                request["flash"](e.args, "error")
            except asyncpg.exceptions.ForeignKeyViolationError as e:
                request["flash"](e.args, "error")
            except asyncpg.exceptions.UniqueViolationError:
                request["flash"](
                    f"{model_id.capitalize()} with id '{row['id']}' already exists",
                    "error",
                )
            except asyncpg.exceptions.NotNullViolationError as e:
                column = e.args[0].split("column")[1].split("violates")[0]
                request["flash"](f"Field {column} cannot be null", "error")
        return response.redirect(f"/admin/{model_id}/")


@admin.route("/login", methods=["GET", "POST"])
async def login(request):
    _login = auth.validate_login(request, cfg.app.config)
    if _login:
        _token = utils.generate_token(request.ip)
        cfg.sessions[_token] = request.headers["User-Agent"]
        request.cookies["auth-token"] = _token
        request["session"] = {"_auth": True}
        _response = jinja.render(
            "index.html", request, objects=cfg.app.db.tables, url_prefix=cfg.URL_PREFIX
        )
        _response.cookies["auth-token"] = _token
        return _response
    else:
        request["flash"]("Password or login is incorrect", "error")
    return jinja.render(
        "login.html", request, objects=cfg.app.db.tables, url_prefix=cfg.URL_PREFIX,
    )


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
    except RuntimeError:
        pass
    jinja.init_app(app)
    cfg.app.config = app.config
