import os
from typing import Callable, List

from gino.ext.sanic import Gino
from jinja2 import FileSystemLoader
from sanic import Blueprint, Sanic
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
