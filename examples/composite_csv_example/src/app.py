import os

from db import Address, Camp, City, Country, Education, Place, db
from sanic import Sanic, response

from gino_admin import add_admin_panel

app = Sanic(name=__name__)
app.config["ADMIN_USER"] = "admin"
app.config["ADMIN_PASSWORD"] = "1234"

app.config["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
app.config["DB_DATABASE"] = "gino"
app.config["DB_USER"] = "gino"
app.config["DB_PASSWORD"] = "gino"

# set os.environ["ADMIN_AUTH_DISABLE"] = "1" to disable auth
db.init_app(app)


@app.route("/")
async def index(request):
    return response.redirect("/admin")


current_path = os.path.dirname(os.path.abspath(__file__))


add_admin_panel(
    app,
    db,
    [Place, City, Camp, Education, Address, Country],
    composite_csv_settings={
        "area": {"models": (Place, Education, Camp), "type_column": "type"}
    },
    presets_folder=os.path.join(current_path, "csv_to_upload"),
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000), debug=True)
