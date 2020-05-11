import os
from typing import Callable, Dict, List, Text

from gino.ext.sanic import Gino
from jinja2 import FileSystemLoader
from sanic import Blueprint, Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin.utils import cfg

loader = FileSystemLoader(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)

jinja = SanicJinja2(loader=loader)

cfg.jinja = jinja


admin = Blueprint("admin", url_prefix=cfg.URL_PREFIX)


admin.static(
    "/static", os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
)


def add_admin_panel(
    app: Sanic,
    db: Gino,
    gino_models: List,
    custom_hash_method: Callable = None,
    presets_folder: Text = "presets",
    *args,
    **kwargs
):
    """ init admin panel and configure """

    cfg.models = {model.__tablename__: model for model in gino_models}
    cfg.app.db = db
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
