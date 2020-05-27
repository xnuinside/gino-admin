import os

from db import City, Country, GiftCard, Item, Place, User, db
from sanic import Sanic, response

from gino_admin import add_admin_panel

app = Sanic()
app.config["ADMIN_USER"] = "admin"
app.config["ADMIN_PASSWORD"] = "1234"

app.config["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
app.config["DB_DATABASE"] = "gino"
app.config["DB_USER"] = "gino"
app.config["DB_PASSWORD"] = "gino"

db.init_app(app)


@app.route("/")
async def index(request):
    return response.redirect("/admin")


current_path = os.path.dirname(os.path.abspath(__file__))


add_admin_panel(
    app,
    db,
    [User, Place, City, GiftCard, Country, Item],
    # any Gino Admin Config params
    presets_folder=os.path.join(current_path, "csv_to_upload"),
    name="Demo Gino Admin Panel",
    route="/gino_admin_demo",
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000), debug=True)
