import os

# import module with your models
import models

from gino_admin import create_admin_app

# gino admin uses Sanic as a framework, so you can define most params as environment variables with 'SANIC_' prefix
# in example used this way to define DB credentials & login-password to admin panel

# but you can use 'db_uri' in config to define creds for Database
# check examples/colored_ui/src/app.py as example

os.environ["SANIC_DB_HOST"] = os.getenv("DB_HOST", "localhost")
os.environ["SANIC_DB_DATABASE"] = "gino"
os.environ["SANIC_DB_USER"] = "gino"
os.environ["SANIC_DB_PASSWORD"] = "gino"


os.environ["SANIC_ADMIN_USER"] = "admin"
os.environ["SANIC_ADMIN_PASSWORD"] = "1234"

current_path = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    # host & port - will be used to up on them admin app
    # config - Gino Admin configuration - check docs to see all possible properties,
    # that allow set path to presets folder or custom_hash_method, optional parameter
    # db_models - list of db.Models classes (tables) that you want to see in Admin Panel
    create_admin_app(
        host="0.0.0.0",
        port=os.getenv("PORT", 5000),
        db=models.db,
        db_models=[models.User, models.City, models.GiftCard, models.Country],
        config={"presets_folder": os.path.join(current_path, "csv_to_upload")},
    )
