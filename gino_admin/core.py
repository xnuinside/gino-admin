import os
from typing import Callable, Dict, List, Text

from gino.ext.sanic import Gino
from jinja2 import FileSystemLoader
from sanic import Blueprint, Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin.utils import cfg, types_map

loader = FileSystemLoader(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)

jinja = SanicJinja2(loader=loader)

cfg.jinja = jinja


admin = Blueprint("admin", url_prefix=cfg.URL_PREFIX)


admin.static(
    "/static", os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
)


def extract_column_data(model_id: Text):
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

        columns_data[name] = {
            "type": type_,
            "nullable": column.nullable,
            "unique": column.unique,
        }
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False
    ]
    unique = [key for key, value in columns_data.items() if value["unique"] is True]
    column_details = {
        "unique_column": unique,
        "required_columns": required,
        "columns_data": columns_data,
        "columns_names": list(columns_data.keys()),
        "hashed_indexes": hashed_indexes,
    }
    return column_details


def create_database_metadata(db: Gino, db_models: List):
    """ extract required data about DB Models """
    cfg.models = {model.__tablename__: {"model": model} for model in db_models}
    cfg.app.db = db

    for model_id in cfg.models:
        column_details = extract_column_data(model_id)
        cfg.models[model_id].update(column_details)


def add_admin_panel(
    app: Sanic,
    db: Gino,
    db_models: List,
    custom_hash_method: Callable = None,
    presets_folder: Text = "presets",
    *args,
    **kwargs
):
    """ init admin panel and configure """

    create_database_metadata(db, db_models)
    cfg.presets_folder = presets_folder
    app.blueprint(admin)
    if custom_hash_method:
        cfg.hash_method = custom_hash_method
    jinja.init_app(app)
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
    if "debug" not in config:
        config["debug"] = True
    return init_admin_app(host, port, db, db_models, config)


def init_admin_app(host, port, db, db_models, config):
    """ init admin panel app """
    app = Sanic()

    db.init_app(app)

    @app.route("/")
    async def index(request):
        return response.redirect("/admin")

    add_admin_panel(app, db, db_models, **config)

    return app.run(host=host, port=port, debug=config["debug"])
