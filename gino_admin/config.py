import os
from typing import Callable, Dict, List, Optional, Text

from expiring_dict import ExpiringDict
from jinja2 import FileSystemLoader
from passlib.hash import pbkdf2_sha256
from pydantic import BaseConfig, BaseModel, validator
from sanic import request
from sanic.response import html
from sanic_jinja2 import SanicJinja2

__version__ = "0.2.4"

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

TEMPLATES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

loader = FileSystemLoader(TEMPLATES_FOLDER)


def render_with_updated_context(
    self,
    template: Text,
    request: request.Request,
    status: int = 200,
    headers: Optional[Dict] = None,
    **context: Dict
):
    context["admin_panel_title"] = cfg.name
    context["objects"] = cfg.user_models
    context["url_prefix"] = cfg.route
    context["admin_panel_version"] = __version__
    context["round_number"] = cfg.round_number
    context["admin_users_route"] = cfg.admin_users_table_name
    context["cfg"] = cfg
    return html(
        self.render_string(template, request, **context),
        status=status,
        headers=headers,
    )


SanicJinja2.render = render_with_updated_context

jinja = SanicJinja2(loader=loader)


class CompositeCsvSettings(BaseModel):
    ...
    # todo


class App:
    """ class to store links to main app data app.config and DB"""

    config = {}
    db = None


class ColorSchema(BaseModel):
    table: Text = "teal"
    table_alert: Text = "orange"
    buttons: Text = "teal"
    buttons_second: Text = "purple"
    buttons_alert: Text = "orange inverted"
    footer: Text = "black"
    header: Text = "black"


class UIConfig(BaseModel):
    colors: ColorSchema = None


class Config(BaseModel):
    """ Gino Admin Panel settings """

    route: str = "/admin"
    jinja: SanicJinja2 = jinja
    app: App = App
    hash_method: Callable = pbkdf2_sha256.encrypt
    models: Dict = {}
    user_models: Dict = {}
    sessions: Dict = {}
    # upload from csv config
    upload_dir: str = "files/"
    max_file_size: int = 10485760
    allowed_file_types: List[str] = ["csv"]
    date_str_formats: List[str] = ["%Y-%m-%d", "%d-%m-%Y", "%Y-%d-%m", "%m-%d-%Y"]
    time_str_formats: List[str] = [
        "%H:%M:%S.%f",
        "%H:%M:%S",
        "%I:%M %p",
        "%I:%M:%S %p",
        "%I:%M:%S.%f %p",
        "%I:%M:%S",
    ]
    datetime_str_formats: List[str] = [
        "%B %d, %Y %I:%M %p",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%m-%d-%yT%H:%M:%S.%f",
        "%m-%d-%y %H:%M:%S",
        "%m-%d-%yT%H:%M:%S",
    ]
    presets_folder: str = "presets"
    presets: Dict = {}
    composite_csv_settings: Dict = {}
    history_table_name: str = "gino_admin_history"
    admin_users_table_name: str = "gino_admin_users"
    admin_roles_table_name: str = "gino_admin_roles"
    name: str = "Sanic-Gino Admin Panel"
    csv_update_existed: bool = True
    debug: bool = True
    displayable_setting: list = [
        "debug",
        "presets_folder",
        "composite_csv_settings",
        "name",
        "csv_update_existed",
    ]
    round_number: float = 3
    history_model: object = None
    admin_user_model: object = None
    users_model: Dict[str, object] = {}
    history_data_columns: List[str] = []
    admin_users_data_columns: List[str] = []
    ui: UIConfig = None
    track_history_endpoints: List[str] = [
        "model_delete",
        "model_delete_all",
        "model_edit_post",
        "model_add",
        "presets_use",
        "init_db_run",
        "file_upload",
        "sql_query_run",
        "login",
        "logout_post",
    ]

    @validator("displayable_setting")
    def displayable_setting_cannot_be_changed(cls, value):
        return ["presets_folder", "composite_csv_settings", "name"]

    class Config(BaseConfig):
        arbitrary_types_allowed = True


# instance of config on current run
cfg = Config()
cfg.sessions = ExpiringDict(ttl=3600)
cfg.jinja = jinja
cfg.ui = UIConfig(colors=ColorSchema())
