from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from starlette.responses import JSONResponse

from db.crud.users import blacklist_token
from db.schemas.users import UserSignUp, User
from db.session import get_db

from core import security
from core.auth import authenticate_user, get_current_active_user, sign_up_new_user

auth_router = r = APIRouter()

# TODO:
# 1. POST /login
#    - generate siging_request, return signing_request url
# 2. POST /signing_request/{request_id}
#    - return a ergoauth signing_request from redis
# 3. POST /token used for ergoauth login for nautilus
#    - verify address, signed_message and proof directly and return a jwt_token 
# 4. WebSocket /ws/{request_id}
#    - Frontend listens to this websocket for approval on mobile app


@r.post("/token/admin", name="auth:admin-login")
async def login_admin(
    db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        if user.is_superuser:
            permissions = "admin"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin only endpoint",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = security.create_access_token(
            data={"sub": user.alias, "permissions": permissions},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer", "permissions": permissions}
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


@r.post("/signup", response_model=User, response_model_exclude_none=True, name="auth:signup")
async def signup(
    user: UserSignUp,
    db=Depends(get_db)
):
    try:
        user = sign_up_new_user(db, user.alias, "__ergoauth_default", user.profile_img_url, user.primary_wallet_address)
        if not user:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="User already exists")
        return user
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::signup::{str(e)}")


@r.post("/signup/admin", name="auth:admin-signup")
async def signup_admin(
    db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        user = sign_up_new_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account already exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        if user.is_superuser:
            permissions = "admin"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin only endpoint",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = security.create_access_token(
            data={"sub": user.alias, "permissions": permissions},
            expires_delta=access_token_expires,
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::signup::{str(e)}")


@r.post("/logout", name="auth:logout")
async def logout(db=Depends(get_db), token: str = Depends(security.oauth2_scheme), current_user=Depends(get_current_active_user)):
    try:
        return blacklist_token(db, token)
    except Exception as e:
        JSONResponse(status_code=400, content=f"ERR::logout::{str(e)}")
