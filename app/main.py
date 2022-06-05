import uvicorn
import databases

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker

# from config import Config, Network
from config import Config, Network
CFG = Config[Network]
DATABASE_URL = CFG.connectionString


database = databases.Database(DATABASE_URL)
Base: DeclarativeMeta = declarative_base()

engine = create_async_engine(DATABASE_URL, connect_args={
                             "check_same_thread": False})

app = FastAPI(
    title="paideia-api",
    docs_url="/api/docs",
    openapi_url="/api"
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# origins = ["*"]
origins = [
    "https://*.paideia.im",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# catch all route (useful?)
# @app.api_route("/{path_name:path}", methods=["GET"])
# async def catch_all(request: Request, path_name: str):
#     return {"request_method": request.method, "path_name": path_name}


@app.get("/api/ping")
async def ping():
    return {"hello": "world"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
