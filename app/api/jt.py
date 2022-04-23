import utcnow
import psycopg2
import asyncio, aiohttp

from starlette.responses import JSONResponse
from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlmodel import Field, Session, select, delete
from datetime import datetime

from db import Engine, SQLModel
import models

from config import Config, Network

CFG = Config[Network]

jt_router = r = APIRouter()

DEBUG = CFG.debug
NOW = utcnow()
DATABASE = CFG.connectionString

# %% CLASSES
@r.get("/info", name="jt:info")
async def info(word: str):
    return {'hello': 'world'}

