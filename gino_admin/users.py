import datetime

from gino_admin import config
from gino_admin.core import extract_column_data

cfg = config.cfg


async def add_users_model(db):
    if "gino_admin_users" not in db.tables:

        class GinoAdminUser(db.Model):

            __tablename__ = cfg.admin_users_table_name
            login = db.Column(db.String(), unique=True, primary_key=True)
            password_hash = db.Column(db.String())
            added_at = db.Column(db.DateTime(), default=datetime.datetime.utcnow())

        schema = db.schema + "." if db.schema else ""

        table_name = schema + cfg.admin_users_table_name
        cfg.admin_user_model = GinoAdminUser
        cfg.models["gino_admin_users"] = {"model": GinoAdminUser}
        column_details = extract_column_data("gino_admin_users")
        cfg.models["gino_admin_users"].update(column_details)
        cfg.admin_users_data_columns = [
            column.name for num, column in enumerate(db.tables[table_name].columns)
        ]
