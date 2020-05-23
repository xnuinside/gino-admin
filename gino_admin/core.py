import os
from copy import deepcopy
from typing import Dict, List, Text

from gino.ext.sanic import Gino
from sanic import Blueprint, Sanic, response
from sanic_jwt import Initialize

from gino_admin import config
from gino_admin.auth import authenticate
from gino_admin.routes import rest
from gino_admin.utils import GinoAdminError, logger, types_map

cfg = config.cfg


admin = Blueprint("admin", url_prefix=cfg.URL_PREFIX)


admin.static(
    "/static", os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
)


def extract_column_data(model_id: Text) -> Dict:
    """ extract data about column """
    _hash = "_hash"
    columns_data, hashed_indexes = {}, []
    for num, column in enumerate(cfg.app.db.tables[model_id].columns):

        if _hash in column.name:
            name = column.name.split(_hash)[0]
            type_ = "HASH"
            hashed_indexes.append(num)
        else:
            name = column.name
            type_ = types_map.get(str(column.type).split("(")[0], str)
        if len(str(column.type).split("(")) > 1:
            len_ = int(str(column.type).split("(")[1].split(")")[0])
        else:
            len_ = None
        columns_data[name] = {
            "type": type_,
            "len": len_,
            "nullable": column.nullable,
            "unique": column.unique,
            "foreign_keys": column.foreign_keys,
        }
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False
    ]
    unique = [key for key, value in columns_data.items() if value["unique"] is True]
    foreign_keys = {}
    for column_name, data in columns_data.items():
        for key in data["foreign_keys"]:
            foreign_keys[key._colspec.split(".")[0]] = (
                column_name,
                key._colspec.split(".")[1],
            )
    columns_details = {
        "unique_columns": unique,
        "required_columns": required,
        "columns_data": columns_data,
        "columns_names": list(columns_data.keys()),
        "hashed_indexes": hashed_indexes,
        "foreign_keys": foreign_keys,
    }
    return columns_details


def extract_models_metadata(db: Gino, db_models: List) -> None:
    """ extract required data about DB Models """
    cfg.models = {model.__tablename__: {"model": model} for model in db_models}
    cfg.app.db = db

    models_to_remove = []

    for model_id in cfg.models:
        column_details = extract_column_data(model_id)
        if not column_details["unique_columns"]:
            models_to_remove.append(model_id)
        else:
            cfg.models[model_id].update(column_details)
            cfg.models[model_id]["key"] = cfg.models[model_id]["unique_columns"][0]

    for model_id in models_to_remove:
        logger.warning(
            f"\nWARNING: Model {model_id.capitalize()} will not be displayed in Admin Panel "
            f"because does not contains any unique column\n"
        )
        del cfg.models[model_id]


def add_admin_panel(app: Sanic, db: Gino, db_models: List, **config_settings):
    """ init admin panel and configure """
    if "custom_hash_method" in config_settings:
        logger.warning(
            f"'custom_hash_method' will be depricated in version 0.1.0. "
            f" Please use 'hash_method' instead"
        )
        config_settings["hash_method"] = deepcopy(config_settings["custom_hash_method"])
        del config_settings["custom_hash_method"]
    for key in config_settings:
        try:
            setattr(cfg, key, config_settings[key])
        except ValueError as e:
            raise GinoAdminError(
                "Error During Gino Admin Panel Initialisation. "
                "You trying to set upWrong config parameters: "
                f"{e}"
            )

    extract_models_metadata(db, db_models)
    app.blueprint(admin)
    app.blueprint(rest.api)
    Initialize(app, authenticate=authenticate, url_prefix="admin/api/auth")
    Initialize(rest.api, app=app, authenticate=authenticate, auth_mode=True)
    cfg.jinja.init_app(app)
    cfg.app.config = app.config


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
    app = Sanic()

    db.init_app(app)

    @app.route("/")
    async def index(request):
        return response.redirect("/admin")

    add_admin_panel(app, db, db_models, **config)

    return app.run(host=host, port=port, debug=cfg.debug)
