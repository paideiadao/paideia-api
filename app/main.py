# %% IMPORTS
import uvicorn
import sqlalchemy as sa
import databases
import asyncpg

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator, Optional
from fastapi_users import models as user_models
from fastapi_users import db as users_db
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker

from api.dao import dao_router
from api.jt import jt_router

# from config import Config, Network
from config import Config, Network
CFG = Config[Network]
DATABASE_URL = CFG.connectionString
SECRET = "hell0w0rld"

class User(user_models.BaseUser):
    name: Optional[str]

class UserCreate(user_models.BaseUserCreate):
    name: str

class UserUpdate(User, user_models.BaseUserUpdate):
    pass

class UserDB(User, user_models.BaseUserDB):
    pass

database = databases.Database(DATABASE_URL)
Base: DeclarativeMeta = declarative_base()

class UserTable(Base, users_db.SQLAlchemyBaseUserTable):
    name = sa.Column(
        sa.String(length=100),
        server_default=sa.sql.expression.literal("No name given"),
        nullable=False,
    )

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
users = UserTable.__table__
user_db = users_db.SQLAlchemyUserDatabase(UserDB, database, users)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=CookieTransport(),
    get_strategy=get_jwt_strategy,
)

class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET
    
    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
    
    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")
    
    async def on_after_request_verify(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(UserDB, session, UserTable)

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# %% APP
app = FastAPI(
    # title=config.PROJECT_NAME,
    docs_url="/api/docs",
    openapi_url="/api"
)

fastapi_users = FastAPIUsers(
    get_user_manager,
    [auth_backend],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# %% INIT
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])

app.include_router(dao_router, prefix='/api/dao', tags=['dao'])
app.include_router(jt_router, prefix='/api/jt', tags=['jt'])

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

# %% FUNCTIONS
@app.get("/api/ping")
async def ping():
    return {"hello": "world"}

# %% MAIN
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=5000)
