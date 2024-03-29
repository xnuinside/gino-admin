from gino.ext.sanic import Gino
from sqlalchemy.dialects.postgresql import JSON, JSONB

db = Gino()


class GiftCard(db.Model):
    __tablename__ = "gifts"
    # class to test different types support
    id = db.Column(db.BigInteger(), unique=True, primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey("users.id"))
    balance = db.Column(db.Integer(), default=0)
    rate = db.Column(db.Numeric())
    rate_3 = db.Column(db.Float())
    created_at = db.Column(db.DateTime())
    magic_date = db.Column(db.Date())
    active = db.Column(db.Boolean())


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.String(), unique=True, primary_key=True)
    password_hash = db.Column(db.String(), nullable=False)
    email = db.Column(db.String())
    name = db.Column(db.String())
    phone = db.Column(db.String())
    address = db.Column(db.String())


class Place(db.Model):

    __tablename__ = "places"

    id = db.Column(db.String(), unique=True, primary_key=True)
    title = db.Column(db.String())
    description = db.Column(db.String())
    owner = db.Column(db.String(24), db.ForeignKey("users.id"))
    hide_column_sample = db.Column(db.String())


class Item(db.Model):

    __tablename__ = "items"

    id = db.Column(db.String(24), unique=True, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String())
    place = db.Column(db.String(24), db.ForeignKey("places.id"))
    time = db.Column(db.Time(), nullable=False)
    additional_data_jsob_b = db.Column(JSONB, nullable=False, server_default="{}")
    additional_data = db.Column(JSON, nullable=False, server_default="{}")


class Country(db.Model):

    __tablename__ = "countries"

    code = db.Column(db.String(8), unique=True, primary_key=True)
    country = db.Column(db.String())
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())


class City(db.Model):

    __tablename__ = "cities"

    # does not contain 'unique' column - so this Model will not showed in UI in Admin Panel
    id = db.Column(db.String())
    country = db.Column(db.String())
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())
