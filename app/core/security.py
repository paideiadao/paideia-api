import time
import secrets
import hashlib
import jwt

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta

from config import Config, Network

CFG = Config[Network]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/beta/auth/admin/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = CFG.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60   # 24 hours


def get_md5_hash(string: str) -> str:
    return hashlib.md5(string.encode("utf-8")).hexdigest()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ergoauth stuff


def generate_verification_id() -> str:
    # a UUID for the request and
    # save the used sigmaBoolean and signing message. The UUID should be
    # path variable for the reply to address and used to fetch the SigmaBoolean
    # and signingMessage data
    return secrets.token_urlsafe()


def generate_signing_message() -> str:
    # we need a message to sign. This message should be unique for our dApp,
    # never occur twice and should not be predictable, so we use a timestring, a unique name
    # and a random component
    return str(secrets.token_urlsafe() + CFG.ergoauth_seed + str(int(time.time())))
