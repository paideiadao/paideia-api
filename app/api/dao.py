# %% IMPORT
import utcnow
import psycopg2
import asyncio, aiohttp
import models

from starlette.responses import JSONResponse
from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlmodel import Field, Session, select, delete
from datetime import datetime
from db import Engine, SQLModel
from config import Config, Network

# %% LOGGING
from log import LogConfig, myself, logging
from logging.config import dictConfig
dictConfig(LogConfig().dict())
log = logging.getLogger("paideia")

CFG = Config[Network]

dao_router = r = APIRouter()

# %% CONFIG
"""
dao
---------------
Lorem ipsum...
"""

# %% INIT
DEBUG = CFG.debug
NOW = utcnow()
DATABASE = CFG.connectionString

# %% CLASSES
class Dao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


# %% ENDPOINTS
@r.get("/info", name="dao:info")
async def info(word: str):
    try:
        log.info('starting...')
        if word:
            return {
                'status': 'success',
                'word': word,
            }
        else:
            raise('word not found')

    except Exception as e:
        log.error(f'ERR:{myself()}: exception in main ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: exception in main ({e})')

# %% MAIN
async def main(eng, mdls):
    """ 
    Display available exmple data from mdls
    """
    try:
        with Session(eng) as session:
            for name, mdl in mdls:
                sql = select(mdl).where(mdl.id < -1)
                res = session.exec(sql).one()
                log.debug(f'{name} - id: {res.id}, name: {res.name}')

    except Exception as e:
        log.error(f'ERR:{myself()}: exception in main ({e})')
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'ERR:{myself()}: exception in main ({e})')

if __name__ == '__main__':
    Models = {
        'DAO': Dao
    }
    asyncio.run(main(Engine, Models))
