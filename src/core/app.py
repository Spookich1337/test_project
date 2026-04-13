from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

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


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


app.include_router(user.router)
app.include_router(note.router)
app.include_router(authorization.router)

current_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(current_dir, "index.html")
@app.get("/")
async def root():
    return FileResponse(html_path)