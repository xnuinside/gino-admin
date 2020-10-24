import os

from db import City, Country, GiftCard, Item, Place, User, db
from passlib.hash import pbkdf2_sha256
from sanic import Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin import add_admin_panel

app = Sanic(name=__name__)
app.config["ADMIN_USER"] = "admin"
app.config["ADMIN_PASSWORD"] = "1234"

app.config["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
app.config["DB_DATABASE"] = "gino"
app.config["DB_USER"] = "gino"
app.config["DB_PASSWORD"] = "gino"

db.init_app(app)

jinja = SanicJinja2(app)


@app.route("/")
async def index(request):
    return response.redirect("/admin")


@app.route("/ui")
async def ui_test(request):
    return jinja.render("index.html", request)


# custom_hash_method you can define your own hash method to use it in backend and Admin
def custom_hash_method(*args, **kwargs):
    print("My custom hash method! Must return python callable object")
    return pbkdf2_sha256.hash(*args, **kwargs)


current_path = os.path.dirname(os.path.abspath(__file__))


add_admin_panel(
    app,
    db,
    [User, Place, City, GiftCard, Country, Item],
    # any Gino Admin Config params
    hash_method=custom_hash_method,
    presets_folder=os.path.join(current_path, "csv_to_upload"),
    name="Base Example",
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000), debug=True)
