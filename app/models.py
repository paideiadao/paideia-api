# %% IMPORTS
import utcnow
import psycopg2
import asyncio, aiohttp

from typing import Optional
from sqlmodel import Field, Session, select
from config import Config, Network
from db import Engine, SQLModel
# from log import log

# %% INIT
CFG = Config[Network]
DEBUG = CFG.debug
NOW = utcnow()
DATABASE = CFG.connectionString

# %% CLASSES
class Generic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

# %% MAIN
async def main(eng, mdl):
    try:
        with Session(eng) as session:
            sql = select(mdl).all()
            res = session.exec(sql)
            logging.debug(f'rows in model: {res.rowcount}')

    except Exception as e:
        logging.error(f'ERR:{myself()}: exception in main ({e})')

if __name__ == '__main__':
    asyncio.run(main(Engine, Dao))
