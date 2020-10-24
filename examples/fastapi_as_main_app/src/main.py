from fastapi import FastAPI
from models import User, db

app = FastAPI()

db.init_app(app)


@app.get("/")
async def root():
    # count number of users in DB
    return {"hello": "Hello!"}


@app.get("/users")
async def users():
    # count number of users in DB
    return {"count_users": await db.func.count(User.id).gino.scalar()}
