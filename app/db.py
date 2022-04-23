import utcnow
import psycopg2
import asyncio

from sqlmodel import SQLModel, create_engine
from config import Config, Network

CFG = Config[Network]
DATABASE = CFG.connectionString

Engine = create_engine(DATABASE)

# %% MAIN
async def main(eng):
    SQLModel.metadata.create_all(eng)

if __name__ == '__main__':
    asyncio.run(main(Engine))
