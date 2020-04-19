from gino.ext.sanic import Gino

db = Gino()


class User(db.Model):

    __tablename__ = "users"

    user_id = db.Column(db.String(24), unique=True, primary_key=True)
    password = db.Column(db.String())
    email = db.Column(db.String(24))
    name = db.Column(db.String())
    phone = db.Column(db.String())
    address = db.Column(db.String())


class Place(db.Model):

    __tablename__ = "places"

    id = db.Column(db.String(24), unique=True, primary_key=True)
    title = db.Column(db.String())
    description = db.Column(db.String())


class City(db.Model):

    __tablename__ = "cities"

    id = db.Column(db.String(24), unique=True, primary_key=True)
    country = db.Column(db.DateTime())
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())
