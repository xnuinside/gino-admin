import os
from copy import deepcopy
from typing import Dict, List, Text

from gino.ext.sanic import Gino
from sanic import Blueprint, Sanic, response, router
from sanic_jwt import Initialize

from gino_admin import config
from gino_admin.auth import authenticate
from gino_admin.history import add_history_model
from gino_admin.users import add_users_model
from gino_admin.routes import rest
from gino_admin.utils import GinoAdminError, logger, types_map, get_table_name, HashColumn

cfg = config.cfg


admin = Blueprint("admin", url_prefix=cfg.route)

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

admin.static("/static", STATIC_FOLDER)
admin.static("/favicon.ico", os.path.join(STATIC_FOLDER, "favicon.ico"))


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
            "db_type": column.type
        }
    required = [
        key for key, value in columns_data.items() if value["nullable"] is False or value["primary"]
    ]
    unique_keys = [key for key, value in columns_data.items() if value["unique"] is True]
    foreign_keys = {}
    for column_name, data in columns_data.items():
        for key in data["foreign_keys"]:
            foreign_keys[key._colspec.split(".")[0]] = (
                column_name,
                key._colspec.split(".")[1],
            )
    
    primary_keys = [key for key, value in columns_data.items() if value["primary"] is True]
    table_details = {
        "unique_columns": unique_keys,
        "required_columns": required,
        "columns_data": columns_data,
        "primary_keys": primary_keys,
        "columns_names": list(columns_data.keys()),
        "hashed_indexes": hashed_indexes,
        "foreign_keys": foreign_keys,
        "identity": primary_keys if primary_keys else unique_keys
        
    }
    return table_details


def extract_models_metadata(db: Gino, db_models: List) -> None:
    """ extract required data about DB Models """
    db_models.append(cfg.users_model)
    cfg.models = {model.__tablename__: {"model": model} for model in db_models}
    cfg.app.db = db
    
    for model_id in cfg.models:
        column_details = extract_column_data(model_id)
        cfg.models[model_id].update(column_details)


def add_admin_panel(app: Sanic, db: Gino, db_models: List, **config_settings):
    """ init admin panel and configure """
    if "custom_hash_method" in config_settings:
        logger.warning(
            f"'custom_hash_method' will be depricated in version 0.1.0. "
            f" Please use 'hash_method' instead"
        )
        config_settings["hash_method"] = deepcopy(config_settings["custom_hash_method"])
        del config_settings["custom_hash_method"]

    if not app.config.get("DB_HOST", None):
        # mean user define path to DB with one-line uri
        config = parse_db_uri(config_settings)
    
    if 'db_uri' in config_settings:
        del config_settings['db_uri']

    for key in config_settings:
        try:
            setattr(cfg, key, config_settings[key])
        except ValueError as e:
            raise GinoAdminError(
                "Error During Gino Admin Panel Initialisation. "
                "You trying to set upWrong config parameters: "
                f"{e}"
            )

    add_history_model(db)
    import asyncio
    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(add_users_model(db, app.config))

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

def parse_db_uri(config: Dict) -> None:
    """ parse db uri and set up sanic variables"""
    
    if config.get('db_uri'):
        db_uri = config['db_uri']
    else:
        db_uri = os.environ.get('ADMIN_DB_URI')
    if not db_uri:
        raise Exception(
            "Need to setup DB_URI env variable  with credentianls to access Database or send 'db_uri' in Gino-Admin config.\n"
            "Example: DB_URI=postgresql://local:local@localhost:5432/gino_db")
    db_uri = db_uri.split("postgresql://")[1]
    if '@' in db_uri:
        db_uri = db_uri.split("@")
        host_and_db = db_uri[1].split('/')
        login_and_password = db_uri[0].split(':')
        login = login_and_password[0]
        password = login_and_password[1]
        host = host_and_db[0]
        db = host_and_db[1]
    else:
        db_uri = db_uri.split("/")
        host = db_uri[0]
        db = db_uri[1]
        login, password = None, None
    if ':' in host:
        host = host.split(':')[0]
    os.environ["SANIC_DB_HOST"] = host
    os.environ["SANIC_DB_DATABASE"] = db
    os.environ["SANIC_DB_USER"] = login
    os.environ["SANIC_DB_PASSWORD"] = password
    return config

def init_admin_app(host, port, db, db_models, config):
    """ init admin panel app """
    app = Sanic()

    db.init_app(app)

    @app.route("/")
    async def index(request):
        return response.redirect("/admin")
    
    add_admin_panel(app, db, db_models, **config)

    return app.run(host=host, port=port, debug=cfg.debug)
