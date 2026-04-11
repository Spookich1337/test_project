from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.DB.redis import redis_client
from src.DB.DBconfig import engine, BaseModel
from src.DB.redis import *

from .routers import user, note, authorization



async def db_init():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


@asynccontextmanager
async def lifespan(app:FastAPI):
    await db_init()
    try:
        await redis_client.ping()
    except Exception as e:
        print(f"Redis connection failed:{e}")
    yield   
    await redis_client.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(user.router)
app.include_router(note.router)
app.include_router(authorization.router)