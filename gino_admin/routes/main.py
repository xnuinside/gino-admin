import os
import uuid
from copy import deepcopy
from csv import reader
from datetime import datetime

import asyncpg
from sanic import response

from gino_admin import auth, utils
from gino_admin.core import admin, jinja
from gino_admin.routes.logic import render_model_view
from gino_admin.utils import cfg, extract_columns_data


@admin.route("/")
@auth.token_validation()
@jinja.template("index.html")  # decorator method is staticmethod
async def bp_root(request):
    return jinja.render(
        "index.html", request, objects=cfg.app.db.tables, url_prefix=cfg.URL_PREFIX,
    )


@admin.route("/logout")
@auth.token_validation()
async def logout(request):
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
            "index.html", request, objects=cfg.app.db.tables, url_prefix=cfg.URL_PREFIX
        )
        _response.cookies["auth-token"] = _token
        return _response
    else:
        request["flash"]("Password or login is incorrect", "error")
    return jinja.render(
        "login.html", request, objects=cfg.app.db.tables, url_prefix=cfg.URL_PREFIX,
    )


def handle_no_auth(request):
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
    request_params["id"] = columns_data["id"]["type"](request_params["id"])
    model = cfg.models[model_id]
    # id can be str or int
    if isinstance(request_params["id"], str):
        new_obj_id = request_params["id"] + "_copy_" + uuid.uuid1().hex
    else:
        new_obj_id = request_params["id"] + uuid.uuid1().int
    bas_obj = utils.serialize_dict((await model.get(request_params["id"])).to_dict())
    bas_obj["id"] = new_obj_id
    try:
        await model.create(**bas_obj)
        request["flash"](f"Object with {request_params['id']} was copied", "success")
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        request["flash"](e.args, "error")
    return await render_model_view(request, model_id)


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
                        validate_header = deepcopy(header)
                        for _num, name in enumerate(validate_header):
                            if name in hashed_columns_names:
                                validate_header[_num] = name + "_hash"
                            if name not in columns_names:
                                request["flash"](
                                    f"Wrong columns in CSV file. Header did not much model's columns. "
                                    f"For {model_id.capitalize()} possible columns {columns_names}",
                                    "error",
                                )
                                return response.redirect(f"/admin/{model_id}/")
                    else:
                        row = {header[index]: value for index, value in enumerate(row)}
                        row = utils.reverse_hash_names(
                            hashed_indexes, columns_names, row
                        )
                        row = utils.correct_types(row, columns_data)
                        try:
                            await cfg.models[model_id].create(**row)
                        except Exception as e:
                            errors.append((num, row["id"], e.args))
                            continue
                        id_added.append(row["id"])
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


@admin.route("/sql_run", methods=["GET"])
@auth.token_validation()
async def sql_query_run_view(request):
    return jinja.render(
        "sql_runner.html",
        request,
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
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
            request["flash"](f"{result}", "success")
        except asyncpg.exceptions.PostgresSyntaxError as e:
            request["flash"](f"{e.args}", "error")
        """rows = await query.gino.all()
        output = []
        for row in rows:
            row = {columns_names[num]: field for num, field in enumerate(row)}
            for index in hashed_indexes:
                row[columns_names[index]] = "*************"

            output.append(row)
        output = output[::-1]
         """
    return jinja.render(
        "sql_runner.html",
        request,
        columns=result,
        objects=cfg.app.db.tables,
        url_prefix=cfg.URL_PREFIX,
    )
