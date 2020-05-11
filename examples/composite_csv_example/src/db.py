from gino.ext.sanic import Gino

db = Gino()


class Education(db.Model):

    __tablename__ = "educations"

    id = db.Column(
        db.String(),
        db.Sequence("incremental_ids", minvalue=0, increment=1),
        unique=True,
    )
    title = db.Column(db.String())
    description = db.Column(db.String())
    address = db.Column(db.BigInteger(), db.ForeignKey("addresses.id"))
    specialisation = db.Column(db.String())


class Camp(db.Model):

    __tablename__ = "camps"

    id = db.Column(
        db.String(),
        db.Sequence("incremental_ids", minvalue=0, increment=1),
        unique=True,
    )
    title = db.Column(db.String())
    description = db.Column(db.String())
    address = db.Column(db.BigInteger(), db.ForeignKey("addresses.id"))
    theme = db.Column(db.String())
    age = db.Column(db.String())


class Place(db.Model):

    __tablename__ = "places"

    id = db.Column(
        db.String(),
        db.Sequence("incremental_ids", minvalue=0, increment=1),
        unique=True,
    )
    title = db.Column(db.String())
    description = db.Column(db.String())
    address = db.Column(db.BigInteger(), db.ForeignKey("addresses.id"))
    category = db.Column(db.String())


class Country(db.Model):

    __tablename__ = "countries"

    code = db.Column(db.String(8), unique=True)
    country = db.Column(db.String())
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())


class City(db.Model):

    __tablename__ = "cities"

    id = db.Column(db.String(), unique=True)
    country = db.Column(db.String(), db.ForeignKey("countries.code"))
    population = db.Column(db.BigInteger())
    location = db.Column(db.String())


class Address(db.Model):

    __tablename__ = "addresses"

    id = db.Column(
        db.BigInteger(),
        db.Sequence("incremental_ids", minvalue=0, increment=1),
        unique=True,
    )
    address = db.Column(db.String())
    city = db.Column(db.String(), db.ForeignKey("cities.id"))


if __name__ == "__main__":
    # to init db
    import sqlalchemy as sa

    db_engine = sa.create_engine("postgresql://gino:gino@localhost:5432/gino")
    db.create_all(bind=db_engine)
    db_engine.dispose()
