from db import User, db
from fastapi import FastAPI

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
