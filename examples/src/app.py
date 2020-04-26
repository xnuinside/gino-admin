from sanic import Sanic, response
from db import db, User, Place, City, GiftCard
from gino_admin import add_admin_panel

from passlib.hash import pbkdf2_sha256


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


# custom_hash_method you can define your own hash method to use it in backend and Admin
def custom_hash_method(*args, **kwargs):
    print('My custom hash method! Must return python callable object')
    return pbkdf2_sha256.hash(*args, **kwargs)


add_admin_panel(app, db, [User, Place, City, GiftCard], custom_hash_method=custom_hash_method)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
