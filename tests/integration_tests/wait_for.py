#!/usr/bin/python
import asyncio
from time import sleep

from gino import Gino


async def main():
    db = Gino()
    await db.set_bind("postgresql://gino:gino@postgres:5432/gino")
    await db.pop_bind().close()


if __name__ == "__main__":
    for _ in range(5):
        try:
            asyncio.get_event_loop().run_until_complete(main())
            print("DB Connected")
            exit(0)
        except Exception as e:
            print(e)
            print("Postgres is not available. Sleep for 8 sec")
            sleep(8)
    else:
        exit(1)
