import os

from db import City, Country, GiftCard, Item, Place, User, db
from sanic import Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin import add_admin_panel

app = Sanic(name=__name__)
app.config["ADMIN_USER"] = "admin"
app.config["ADMIN_PASSWORD"] = "1234"

db.init_app(app)

jinja = SanicJinja2(app)


@app.route("/")
async def index(request):
    return response.redirect("/admin")


current_path = os.path.dirname(os.path.abspath(__file__))


add_admin_panel(
    app,
    db,
    [User, Place, City, GiftCard, Country, Item],
    name="Colored UI",
    config={
        "ui": {"colors": {"buttons": "orange", "buttons_alert": "pink"}},
        "db_uri": "postgresql://gino:gino@localhost:5432/gino",
    },
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000), debug=True)
