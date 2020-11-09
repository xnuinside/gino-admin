import os

import db

from gino_admin import create_admin_app

# os.environ["SANIC_ADMIN_USER"] = "admin"
# os.environ["SANIC_ADMIN_PASSWORD"] = "1234"
os.environ["ADMIN_AUTH_DISABLE"] = "1"  # to disable auth


def create_models_list(models) -> list:
    """ creates list of gino models """
    models_list = []
    for name in dir(models):
        entity = getattr(models, name)
        if getattr(entity, "__tablename__", None):
            models_list.append(entity)
    return models_list


if __name__ == "__main__":
    create_admin_app(
        db.db,
        create_models_list(db),
        port=os.environ.get("PORT", "5000"),
        config={
            "name": "Colored UI",
            "ui": {"colors": {"buttons": "orange", "buttons_alert": "pink"}},
            "db_uri": f"postgresql://gino:gino@{os.environ.get('DB_HOST', 'localhost')}:5432/gino",
        },
    )
