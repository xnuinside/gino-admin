import os

import db
from sanic import Sanic, response
from sanic_jinja2 import SanicJinja2

from gino_admin import add_admin_panel

app = Sanic(name=__name__)
app.config["ADMIN_USER"] = "admin"
app.config["ADMIN_PASSWORD"] = "1234"
# set os.environ["ADMIN_AUTH_DISABLE"] = "1" to disable auth


db.db.init_app(app)

jinja = SanicJinja2(app)


@app.route("/")
async def index(request):
    return response.redirect("/admin")


current_path = os.path.dirname(os.path.abspath(__file__))


def create_models_list(models) -> list:
    """ creates list of gino models """
    models_list = []
    for name in dir(models):
        entity = getattr(models, name)
        if getattr(entity, "__tablename__", None):
            models_list.append(entity)
    return models_list


add_admin_panel(
    app,
    db.db,
    create_models_list(db),
    name="Colored UI",
    config={
        "ui": {"colors": {"buttons": "orange", "buttons_alert": "pink"}},
        "db_uri": "postgresql://gino:gino@localhost:5432/gino",
    },
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("PORT", 5000), debug=True)
