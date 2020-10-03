from gino_admin import config

cfg = config.cfg


def add_users_model(db):
    if "gino_admin_users" not in db.tables:

        class GinoAdminUser(db.Model):

            __tablename__ = cfg.admin_users_table_name

            id = db.Column(
                db.String(),
                db.Sequence("gino_admin_seq_users"),
                unique=True,
                primary_key=True,
            )
            login = db.Column(db.String())
            password_hash = db.Column(db.String())
            added_at = db.Column(db.DateTime())
        schema = db.schema + '.' if db.schema else ''
        
        table_name = schema + cfg.admin_users_table_name
        cfg.users_model = GinoAdminUser
        cfg.admin_users_data_columns = [
            column.name for num, column in enumerate(db.tables[table_name].columns)
        ]