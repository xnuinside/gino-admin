from gino_admin import config

cfg = config.cfg


def add_users_model(db):
    # todo: add in next versions
    if "gino_admin_users" not in db.tables:

        class GinoAdminUser(db.Model):

            __tablename__ = cfg.history_table_name

            id = db.Column(
                db.String(),
                db.Sequence("gino_admin_seq_users"),
                unique=True,
                primary_key=True,
            )
            login = db.Column(db.String())
            password_hash = db.Column(db.String())
            added_at = db.Column(db.DateTime())

        cfg.users_model = GinoAdminUser
        cfg.admin_users_data_columns = [
            column.name for num, column in enumerate(db.tables[cfg.users_model].columns)
        ]
