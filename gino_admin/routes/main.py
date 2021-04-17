import os
from ast import literal_eval
from typing import Text

import asyncpg
from sanic import response
from sanic.request import Request
from sqlalchemy.engine.url import URL

from gino_admin import auth, config, utils
from gino_admin.core import admin
from gino_admin.history import log_history_event, write_history_after_response
from gino_admin.routes.crud import model_view_table
from gino_admin.routes.logic import (count_elements_in_db, create_object_copy,
                                     deepcopy_recursive,
                                     drop_and_recreate_all_tables,
                                     insert_data_from_csv_file,
                                     render_model_view, upload_from_csv_data)
from gino_admin.users import add_users_model

cfg = config.cfg
jinja = cfg.jinja


@admin.listener("after_server_start")
async def before_server_start(_, loop):
    if cfg.app.config.get("DB_DSN"):
        dsn = cfg.app.config.DB_DSN
    else:
        dsn = URL(
            drivername=cfg.app.config.setdefault("DB_DRIVER", "asyncpg"),
            host=cfg.app.config.setdefault("DB_HOST", "localhost"),
            port=cfg.app.config.setdefault("DB_PORT", 5432),
            username=cfg.app.config.setdefault("DB_USER", "postgres"),
            password=cfg.app.config.setdefault("DB_PASSWORD", ""),
            database=cfg.app.config.setdefault("DB_DATABASE", "postgres"),
        )

    await cfg.app.db.set_bind(
        dsn,
        echo=cfg.app.config.setdefault("DB_ECHO", False),
        min_size=cfg.app.config.setdefault("DB_POOL_MIN_SIZE", 5),
        max_size=cfg.app.config.setdefault("DB_POOL_MAX_SIZE", 10),
        ssl=cfg.app.config.setdefault("DB_SSL"),
        loop=loop,
        **cfg.app.config.setdefault("DB_KWARGS", dict()),
    )


@admin.middleware("request")
async def middleware_request(request):
    request.ctx.flash_messages = []
    request.ctx.history_action = {}
    conn = await cfg.app.db.acquire(lazy=True)
    request.ctx.connection = conn


@admin.middleware("response")
async def middleware_response(request, response):
    if (
        request.endpoint.split(".")[-1] in cfg.track_history_endpoints
        and request.method == "POST"
    ):
        await write_history_after_response(request)
    conn = getattr(request.ctx, "connection", None)
    if conn is not None:
        try:
            await conn.release()
        except ValueError:
            pass


@admin.route("/")
@auth.token_validation()
async def bp_root(request):
    return jinja.render("index.html", request)


@admin.route("/logout", methods=["GET"])
async def logout(request: Request):
    request = auth.logout_user(request)
    return jinja.render("login.html", request)


@admin.route("/logout", methods=["POST"])
async def logout_post(request: Request):
    return await login(request)


@admin.route("/login", methods=["GET", "POST"])
async def login(request):
    if not cfg.admin_user_model:
        await add_users_model(cfg.app.db)
    _login, request = await auth.validate_login(request, cfg.app.config)
    if _login:
        _token = utils.generate_token(request.ip)
        cfg.sessions[_token] = {
            "user_agent": request.headers["User-Agent"],
            "user": _login,
        }
        request.cookies["auth-token"] = _token
        request.ctx.session = {"_auth": True}
        _response = jinja.render("index.html", request)
        _response.cookies["auth-token"] = _token
        return _response
    request.ctx.session = {"_flashes": request.ctx.flash_messages}
    return jinja.render("login.html", request)


@admin.listener("before_server_stop")
async def before_server_stop(_, loop):
    conn = cfg.app.db.bind.pop("connection", None)
    if conn is not None:
        await conn.release()


@admin.route("/<model_id>/deepcopy", methods=["POST"])
@auth.token_validation()
async def model_deepcopy(request, model_id):
    """
    Recursively creates copies for the whole chain of entities, referencing the given model and instance id through
    the foreign keys.
    :param request:
    :param model_id:
    :return:
    """
    request_params = {key: request.form[key][0] for key in request.form}

    columns_data = cfg.models[model_id]["columns_data"]
    base_obj_id = utils.extract_obj_id_from_query(request_params["_id"])
    try:
        # todo: fix deepcopy
        new_id = utils.extract_obj_id_from_query(request_params["new_id"])
        new_id = utils.correct_types(new_id, columns_data)
    except ValueError as e:
        request.ctx.flash(e, "error")
        return await render_model_view(request, model_id)
    try:
        async with cfg.app.db.acquire() as conn:
            async with conn.transaction() as _:
                new_base_obj_id = await deepcopy_recursive(
                    cfg.models[model_id]["model"],
                    base_obj_id,
                    new_id=new_id,
                    model_data=cfg.models[model_id],
                )
                if isinstance(new_base_obj_id, tuple):
                    request.ctx.flash(new_base_obj_id, "error")
                else:
                    message = f"Object with {request_params['_id']} was deepcopied with new id {new_base_obj_id}"
                    request.ctx.flash(message, "success")
                    log_history_event(request, message, new_base_obj_id)
    except asyncpg.exceptions.PostgresError as e:
        request.ctx.flash(e.args, "error")
    return await render_model_view(request, model_id)


@admin.route("/<model_id>/copy", methods=["POST"])
@auth.token_validation()
async def model_copy(request, model_id):
    """ route for copy item per row """
    request_params = {elem: request.form[elem][0] for elem in request.form}
    base_obj_id = utils.extract_obj_id_from_query(request_params["_id"])
    try:
        new_obj_key = await create_object_copy(
            model_id, base_obj_id, cfg.models[model_id]
        )
        message = f"Object with {base_obj_id} key was copied as {new_obj_key}"
        flash_message = (message, "success")
        log_history_event(request, message, new_obj_key)
    except asyncpg.exceptions.UniqueViolationError as e:
        flash_message = (
            f"Duplicate in Unique column Error during copy: {e.args}. \n"
            f"Try to rename existed id or add manual.",
            "error",
        )
    except asyncpg.exceptions.ForeignKeyViolationError as e:
        flash_message = (e.args, "error")
    return await model_view_table(request, model_id, flash_message)


@admin.route("/init_db", methods=["GET"])
@auth.token_validation()
async def init_db_view(request: Request):
    return jinja.render("init_db.html", request, data=await count_elements_in_db())


@admin.route("/init_db", methods=["POST"])
@auth.token_validation()
async def init_db_run(request: Request):

    data = literal_eval(request.form["data"][0])
    count = 0
    for _, value in data.items():
        if isinstance(value, int):
            count += value
    await drop_and_recreate_all_tables()
    message = f"{count} object was deleted. DB was Init from Scratch"
    request.ctx.flash(message, "success")
    log_history_event(request, message, "system: init_db")
    return jinja.render("init_db.html", request, data=await count_elements_in_db())


@admin.route("/presets", methods=["GET"])
@auth.token_validation()
async def presets_view(request: Request):
    return jinja.render(
        "presets.html",
        request,
        presets_folder=cfg.presets_folder,
        presets=utils.get_presets()["presets"],
    )


@admin.route("/settings", methods=["GET"])
@auth.token_validation()
async def settings_view(request: Request):
    return jinja.render("settings.html", request, settings=utils.get_settings())


@admin.route("/presets/", methods=["POST"])
@auth.token_validation()
async def presets_use(request: Request):
    preset = utils.get_preset_by_id(request.form["preset"][0])
    with_drop = "with_db" in request.form
    if with_drop:
        await drop_and_recreate_all_tables()
        request.ctx.flash("DB was successful Dropped", "success")
    try:
        for model_id, file_path in preset["files"].items():
            request, is_success = await insert_data_from_csv_file(
                os.path.join(cfg.presets_folder, file_path), model_id.lower(), request
            )
        for message in request.ctx.flash_messages:
            request.ctx.flash(*message)
        history_message = (
            f"Loaded preset {preset['id']} {' with DB drop' if with_drop else ''}"
        )
        log_history_event(request, history_message, "system: load_preset")
    except FileNotFoundError:
        request.ctx.flash(f"Wrong file path in Preset {preset['name']}.", "error")
    return jinja.render("presets.html", request, presets=utils.get_presets()["presets"])


@admin.route("/<model_id>/upload/", methods=["POST"])
@auth.token_validation()
async def file_upload(request: Request, model_id: Text):
    upload_file = request.files.get("file_names")
    file_name = utils.secure_filename(upload_file.name)
    if not upload_file or not file_name:
        flash_message = ("No file chosen to Upload", "error")
        return await model_view_table(request, model_id, flash_message)
    if not utils.valid_file_size(upload_file.body, cfg.max_file_size):
        return response.redirect("/?error=invalid_file_size")
    else:
        request, is_success = await upload_from_csv_data(
            upload_file, file_name, request, model_id
        )
        return await model_view_table(request, model_id, request.ctx.flash_messages)


@admin.route("/sql_run", methods=["GET"])
@auth.token_validation()
async def sql_query_run_view(request):
    return jinja.render("sql_runner.html", request)


@admin.route("/sql_run", methods=["POST"])
@auth.token_validation()
async def sql_query_run(request):
    result = []
    if not request.form.get("sql_query"):
        request.ctx.flash("SQL query cannot be empty", "error")
    else:
        sql_query = request.form["sql_query"][0]
        try:
            result = await cfg.app.db.status(cfg.app.db.text(sql_query))
            log_history_event(request, f"Query run '{sql_query}'", "system: sql_run")
        except asyncpg.exceptions.PostgresSyntaxError as e:
            request.ctx.flash(f"{e.args}", "error")
        except asyncpg.exceptions.UndefinedTableError as e:
            request.ctx.flash(f"{e.args}", "error")
    if result:
        return jinja.render(
            "sql_runner.html", request, columns=result[1], result=result[1]
        )
    else:
        return jinja.render("sql_runner.html", request)


@admin.route("/history", methods=["GET"])
@auth.token_validation()
async def history_display(request):
    model = cfg.app.db.tables[cfg.history_table_name]
    query = cfg.app.db.select([model])
    try:
        rows = await query.gino.all()
    except asyncpg.exceptions.UndefinedTableError:
        await cfg.app.db.gino.create_all(tables=[model])
        rows = await query.gino.all()
    history_data = []
    for row in rows:
        row = {cfg.history_data_columns[num]: field for num, field in enumerate(row)}
        history_data.append(row)
    return jinja.render(
        "history.html",
        request,
        history_data_columns=cfg.history_data_columns,
        history_data=history_data,
    )
