def history_model(db):
    class History(db.Model):

        id = db.Column(db.String(), unique=True, primary_key=True)
        user = db.Column(db.String())
        route = db.Column(db.String())
