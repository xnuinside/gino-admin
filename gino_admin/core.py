import os
from copy import deepcopy
from typing import Dict, List, Text

import sqlalchemy
from gino import Gino
from sanic import Blueprint, Sanic, response, router
from sanic_jwt import Initialize

from gino_admin import config
from gino_admin.auth import authenticate
from gino_admin.history import add_history_model
from gino_admin.routes import rest
from gino_admin.types import types_map
from gino_admin.utils import (GinoAdminError, HashColumn, get_table_name,
                              logger, parse_db_uri)

cfg = config.cfg


admin = Blueprint("admin", url_prefix=cfg.route)


admin.static("/static", config.STATIC_FOLDER)
admin.static("/favicon.ico", os.path.join(config.STATIC_FOLDER, "favicon.ico"))


def extract_column_data(model_id: Text) -> Dict:
    """ extract data about column """
    _hash = "_hash"
    columns_data, hashed_indexes = {}, []
    table_name = get_table_name(model_id)
    for num, column in enumerate(cfg.app.db.tables[table_name].columns):
        if _hash in column.name:
            name = column.name.split(_hash)[0]
            type_ = HashColumn
            hashed_indexes.append(num)
        else:
            name = column.name
            type_ = types_map.get(str(column.type).split("(")[0])
            if not type_:
                logger.error(f"{column.type} was not found in types_map")
                type_ = str
        if len(str(column.type).split("(")) > 1:
            len_ = int(str(column.type).split("(")[1].split(")")[0])
        else:
            len_ = None
        columns_data[name] = {
            "type": type_,
            "len": len_,
            "nullable": column.nullable,
            "unique": column.unique,
            "primary": column.primary_key,
            "foreign_keys": column.foreign_keys,
            "db_type": column.type,
            "sequence": isinstance(column.default, sqlalchemy.sql.schema.Sequence),
        }
    required = [
        key
        for key, value in columns_data.items()
        if value["nullable"] is False or value["primary"]
    ]
    unique_keys = [
        key for key, value in columns_data.items() if value["unique"] is True
    ]
    foreign_keys = {}
    for column_name, data in columns_data.items():
        for key in data["foreign_keys"]:
            foreign_keys[key._colspec.split(".")[0]] = (
                column_name,
                key._colspec.split(".")[1],
            )

    primary_keys = [
        key for key, value in columns_data.items() if value["primary"] is True
    ]
    table_details = {
        "unique_columns": unique_keys,
        "required_columns": required,
        "columns_data": columns_data,
        "primary_keys": primary_keys,
        "columns_names": list(columns_data.keys()),
        "hashed_indexes": hashed_indexes,
        "foreign_keys": foreign_keys,
        "identity": primary_keys,
    }
    return table_details


def extract_models_metadata(db: Gino, db_models: List) -> None:
    """ extract required data about DB Models """
    cfg.user_models = {model.__tablename__: {"model": model} for model in db_models}
    cfg.models.update(cfg.user_models)
    cfg.app.db = db

    for model_id in cfg.models:
        column_details = extract_column_data(model_id)
        cfg.models[model_id].update(column_details)


def add_admin_panel(app: Sanic, db: Gino, db_models: List, **config_settings):
    """ init admin panel and configure """
    if "config" in config_settings:
        config_settings.update(config_settings["config"])
        del config_settings["config"]
    if "custom_hash_method" in config_settings:
        logger.warning(
            "'custom_hash_method' will be depricated in version 0.1.0. "
            " Please use 'hash_method' instead"
        )
        config_settings["hash_method"] = deepcopy(config_settings["custom_hash_method"])
        del config_settings["custom_hash_method"]
    if not app.config.get("DB_HOST", None):
        # mean user define path to DB with one-line uri
        if config_settings.get("db_uri", None):
            parse_db_uri(config_settings["db_uri"])
        else:
            raise Exception(
                "Credentials for DB must be provided"
                "as SANIC config settings or as db_uri arg to Gino-Admin Panel"
            )

    if "db_uri" in config_settings:
        del config_settings["db_uri"]

    setup_config_from_args(config_settings)

    add_history_model(db)
    extract_models_metadata(db, db_models)

    if config_settings.get("route"):
        old_prefix = admin.url_prefix
        admin.url_prefix = config_settings["route"]
        rest.api.url_prefix = str(rest.api.url_prefix).replace(
            old_prefix, config_settings["route"]
        )

    app.blueprint(admin)
    app.blueprint(rest.api)
    try:
        Initialize(app, authenticate=authenticate, url_prefix=f"{cfg.route}/api/auth")
        Initialize(rest.api, app=app, authenticate=authenticate, auth_mode=True)
    except router.RouteExists:
        pass
    # to avoid re-write app Jinja2
    if getattr(app, "extensions", None):
        app_jinja = app.extensions["jinja2"]
    else:
        app_jinja = None
    cfg.jinja.init_app(app)
    if app_jinja:
        app_jinja.init_app(app)
    cfg.app.config = app.config


def setup_config_from_args(config_settings: Dict) -> None:
    for key, value in config_settings.items():
        if key == "ui":
            ui = config.UIConfig(**value)
            ui.colors = config.ColorSchema(**value["colors"])
            value = ui
        try:
            setattr(cfg, key, value)
        except ValueError as e:
            raise GinoAdminError(
                "Error During Gino Admin Panel Initialisation. "
                "You trying to set upWrong config parameters: "
                f"{e}"
            )


def create_admin_app(
    db: Gino,
    db_models: List = None,
    config: Dict = None,
    host: Text = "0.0.0.0",
    port: int = 5000,
):
    """ check provided arguments & create admin panel app """
    if config is None:
        config = {}
    if db_models is None:
        db_models = []

    return init_admin_app(host, port, db, db_models, config)


def init_admin_app(host, port, db, db_models, config):
    """ init admin panel app """
    app = Sanic(name="gino_admin")

    @app.route("/")
    async def index(request):
        return response.redirect("/admin")

    add_admin_panel(app, db, db_models, **config)

    return app.run(host=host, port=port, debug=cfg.debug)
