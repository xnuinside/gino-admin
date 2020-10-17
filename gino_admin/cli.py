import importlib.util
import os
from typing import Text, Dict

import click

from gino_admin import create_admin_app
from gino_admin.utils import parse_db_uri


@click.group()
def cli():
    pass


# todo: change config commands to some stored in one place list
# todo: add check for config values, errors
@click.command(
    name="run",
    help="Up Gino Admin Web Panel. "
    "To run Admin Panel, please provide module with models",
)
@click.option(
    "-g", "--gino_var", default="db", help="Variable what stores Gino() engine."
)
@click.option(
    "-c",
    "--config",
    default="",
    help="Config to use to run Gino Admin. "
    "Can contains fields: [composite_csv_settings, presets_folder, custom_hash_method]",
)
@click.option("-h", "--host", default="0.0.0.0", help="Host to run Gino Admin")
@click.option(
    "--no-auth",
    is_flag=True,
    flag_value=True,
    help="Run Admin Panel with out Auth in UI",
)
@click.option("-u", "--user", default=None, help="Login:password for Admin Panel User")
@click.option("-p", "--port", default=5000, help="Port to use run Gino Admin")
@click.option(
    "-d",
    "--db",
    default=None,
    help="DB credentials in format: "
    "postgresql://%(DB_USER):%(DB_PASSWORD)@%(DB_HOST):%(DB_PORT)/%(DB)",
)
@click.argument("module")
def run_command(module, host, port, config, gino_var, db, no_auth, user):
    click.echo(
        f"Run Gino Admin Panel on host {host} and port {port}. Config: {config}. "
        f"Module with models file: {module}. Gino Engine variable {db}"
    )
    if not os.path.isfile(module):
        # todo: need to add load by python module name
        click.echo(f"Cannot found {module}. Please path to python file with DB Models")
        exit(1)
    spec = importlib.util.spec_from_file_location("db", module)
    module_obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_obj)

    db_models = []

    for name in dir(module_obj):
        if name == gino_var:
            gino_var = getattr(module_obj, name)
            continue
        if not name.startswith("__"):
            mod = getattr(module_obj, name)
            if getattr(mod, "__tablename__", None):
                db_models.append(mod)
    if db:
        parse_db_uri(db)
    if user:
        if len(user.split(":")) <= 1:
            click.echo(
                f"--user must be provided in format login:password. You set {user}"
            )
            exit(1)
        os.environ["SANIC_ADMIN_USER"] = user.split(":")[0]
        os.environ["SANIC_ADMIN_PASSWORD"] = user.split(":")[1]
    click.echo(f"Models that will be displayed in Admin Panel: \n {db_models}")
    if config:
        prepared_config = parse_config_line(config)
        click.echo(f"Run Gino Admin with config: {prepared_config}")
    else:
        prepared_config = {}
    if no_auth:
        os.environ["ADMIN_AUTH_DISABLE"] = "1"
    create_admin_app(gino_var, db_models, prepared_config, host, port)


def parse_config_line(config_str: Text) -> Dict:
    pairs = config_str.split(";")
    prepared_config = {}
    for pair in pairs:
        prepared_config[pair.split("=")[0]] = pair.split("=")[1]
    return prepared_config


cli.add_command(run_command)
