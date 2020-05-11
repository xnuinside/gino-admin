import os
import uuid

# when gino admin runs it set 'GINO_ADMIN' = '1' to get possible check that application used DB Model
# pay attention, that in this case you need to run admin panel and main app in different venvs
if os.environ.get("GINO_ADMIN"):
    from gino.ext.sanic import Gino

    db = Gino()
else:
    from gino.ext.starlette import Gino

    db = Gino(dsn="postgresql://gino:gino@localhost:5432/gino")


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


class Country(db.Model):

    __tablename__ = "countries"

    id = db.Column(db.String(24), unique=True, primary_key=True, default=uuid.uuid4)
    country = db.Column(db.String())
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())


class City(db.Model):

    __tablename__ = "cities"

    id = db.Column(db.String(), unique=True, primary_key=True, default=uuid.uuid4)
    country = db.Column(db.String())
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())


if __name__ == "__main__":
    # to init db
    import sqlalchemy as sa

    db_engine = sa.create_engine("postgresql://gino:gino@localhost:5432/gino")
    db.create_all(bind=db_engine)
    db_engine.dispose()
