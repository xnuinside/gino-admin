from gino import Gino
from sqlalchemy.dialects.postgresql import ARRAY

db = Gino()


class TelegramMessage(db.Model):

    __tablename__ = "telegram_messages"

    id = db.Column(
        db.String(),
        db.Sequence("incremental_ids", minvalue=0, increment=1),
        unique=True,
    )
    text = db.Column(db.Text())


class Chat(db.Model):

    __tablename__ = "chats"

    id = db.Column(db.Integer(), unique=True)
    type = db.Column(db.String())
    name = db.Column(db.String())


class Schedule(db.Model):

    __tablename__ = "schedules"

    id = db.Column(db.String(), db.Sequence("incremental_ids", minvalue=0, increment=1))
    chat_ids = db.Column(ARRAY(db.Integer()))
    message_id = db.Column(db.Text())
    schedule = db.Column(db.DateTime())
