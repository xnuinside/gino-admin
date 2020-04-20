from gino.ext.sanic import Gino
from sqlalchemy.orm import validates

db = Gino()


class User(db.Model):

    __tablename__ = "users"

    user_id = db.Column(db.String(24), unique=True, primary_key=True)
    password_hash = db.Column(db.String(), nullable=False)
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


if __name__ == '__main__':
    # to init db
    import sqlalchemy as sa
    db_engine = sa.create_engine('postgresql://gino:gino@localhost:5432/gino')
    db.create_all(bind=db_engine)
    db_engine.dispose()
