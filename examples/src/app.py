from sanic import Sanic, response
from db import db, User, Place, City
from gino_admin import add_admin_panel

app = Sanic()

app.config['DB_HOST'] = 'localhost'
app.config['DB_DATABASE'] = 'gino'
app.config['DB_USER'] = 'gino'
app.config['DB_PASSWORD'] = 'gino'
db.init_app(app)


@app.route("/")
async def index(request):
    return response.redirect("/admin")

app.config['ADMIN_USER'] = 'admin'
app.config['ADMIN_PASSWORD'] = '1234'

add_admin_panel(app, db, [User, Place, City])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
