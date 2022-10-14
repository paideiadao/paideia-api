from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from ergo_python_appkit.appkit import ErgoAppKit

from db.crud.users import (
    blacklist_token,
    get_user_by_wallet_address,
    get_user_by_wallet_addresses,
    get_primary_wallet_address_by_user_id,
)
from db.schemas.ergoauth import (
    LoginRequestWebResponse,
    LoginRequest,
    LoginRequestMobileResponse,
    ErgoAuthRequest,
    ErgoAuthResponse,
)
from db.session import get_db

from core import security
from core.security import generate_signing_message, generate_verification_id
from core.auth import authenticate_user, get_current_active_user, sign_up_new_user

from cache.cache import cache
from websocket.connection_manager import connection_manager

from config import Config, Network

CFG = Config[Network]

auth_router = r = APIRouter()


##################################
##           ERGOAUTH           ##
##################################


BASE_ERGOAUTH = "ergoauth://192.168.1.10"
BASE_URL = "http://localhost:8000/api"


@r.post("/login", response_model=LoginRequestWebResponse, name="ergoauth:login-web")
async def ergoauth_login_web(addresses: LoginRequest, db=Depends(get_db)):
    try:
        # get primary address by default
        default_address = addresses.addresses[0]
        user = get_user_by_wallet_addresses(db, addresses.addresses)
        if user:
            default_address = get_primary_wallet_address_by_user_id(db, user.id)

        verificationId = generate_verification_id()
        tokenUrl = f"{BASE_URL}/auth/token/{verificationId}"
        ret = LoginRequestWebResponse(
            address=default_address,
            signingMessage=generate_signing_message(),
            tokenUrl=tokenUrl,
        )
        cache.set(f"ergoauth_signing_request_{verificationId}", ret.dict())
        return ret
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


# should we add a response type here
@r.post("/token/{request_id}", name="ergoauth:login")
async def ergoauth_token(
    request_id: str, authResponse: ErgoAuthResponse, db=Depends(get_db)
):
    try:
        signingRequest = cache.get(f"ergoauth_signing_request_{request_id}")
        verified = ErgoAppKit.verifyErgoAuthSignedMessage(
            signingRequest["address"],
            signingRequest["signingMessage"],
            authResponse.signedMessage,
            authResponse.proof,
        )
        user = create_and_get_user_by_primary_wallet_address(
            db, signingRequest["address"]
        )
        if verified and user:
            access_token_expires = timedelta(
                minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            permissions = "user"
            access_token = security.create_access_token(
                data={"sub": user.alias, "permissions": permissions},
                expires_delta=access_token_expires,
            )
            cache.invalidate(f"ergoauth_signing_request_{request_id}")
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "permissions": permissions,
                "id": user.id,
                "alias": user.alias,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cannot Authenticate",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


@r.post(
    "/login/mobile",
    response_model=LoginRequestMobileResponse,
    name="ergoauth:login-mobile",
)
async def ergoauth_login_mobile(addresses: LoginRequest):
    try:
        verificationId = generate_verification_id()
        # update url on deployment
        signingRequestUrl = f"{BASE_ERGOAUTH}/auth/signing_request/{verificationId}"
        replyTo = f"{BASE_URL}/auth/verify/{verificationId}"
        sigmaBoolean = ErgoAppKit.getSigmaBooleanFromAddress(addresses.addresses[0])
        ergoAuthRequest = ErgoAuthRequest(
            address=addresses.addresses[0],
            signingMessage=generate_signing_message(),
            sigmaBoolean=sigmaBoolean,
            replyTo=replyTo,
        )
        cache.set(f"ergoauth_signing_request_{verificationId}", ergoAuthRequest.dict())
        return LoginRequestMobileResponse(
            address=addresses.addresses[0],
            verificationId=verificationId,
            signingRequestUrl=signingRequestUrl,
        )
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


@r.get(
    "/signing_request/{request_id}",
    response_model=ErgoAuthRequest,
    name="ergoauth:signing-request",
)
async def ergoauth_login_mobile(request_id: str):
    try:
        ret = cache.get(f"ergoauth_signing_request_{request_id}")
        if not ret:
            return JSONResponse(
                status_code=400, content=f"ERR::login::invalid request id"
            )
        return ret
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


@r.post("/verify/{request_id}", name="ergoauth:verify")
async def ergoauth_verify(
    request_id: str, authResponse: ErgoAuthResponse, db=Depends(get_db)
):
    try:
        signingRequest = cache.get(f"ergoauth_signing_request_{request_id}")
        verified = ErgoAppKit.verifyErgoAuthSignedMessage(
            signingRequest["address"],
            signingRequest["signingMessage"],
            authResponse.signedMessage,
            authResponse.proof,
        )
        user = create_and_get_user_by_primary_wallet_address(
            db, signingRequest["address"]
        )
        if verified and user:
            # generate the access token
            access_token_expires = timedelta(
                minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            permissions = "user"
            access_token = security.create_access_token(
                data={"sub": user.alias, "permissions": permissions},
                expires_delta=access_token_expires,
            )
            token = {
                "access_token": access_token,
                "token_type": "bearer",
                "permissions": permissions,
                "id": user.id,
                "alias": user.alias,
            }
            # use websockets to notify the frontend
            await connection_manager.send_personal_message(
                "ergoauth_" + request_id, token
            )
            # invalidate the the request_id
            cache.invalidate(f"ergoauth_signing_request_{request_id}")
            return {"status": "ok"}
        else:
            # notify frontend on failure
            permissions = "login_error"
            await connection_manager.send_personal_message(
                "ergoauth_" + request_id, {"permissions": permissions}
            )
            return {"status": "failed"}
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


@r.websocket("/ws/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    await connection_manager.connect("ergoauth_" + request_id, websocket)
    try:
        while True:
            # pause loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect("ergoauth_" + request_id)


# [DEPRECATED]
# @r.post("/signup", response_model=User, response_model_exclude_none=True, name="ergoauth:signup")
# async def signup(
#     user: UserSignUp,
#     db=Depends(get_db)
# ):
#     try:
#         user = sign_up_new_user(db, user.alias, "__ergoauth_default", user.profile_img_url, user.primary_wallet_address)
#         if not user:
#             return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="Account already exists")
#         return user
#     except Exception as e:
#         return JSONResponse(status_code=400, content=f"ERR::signup::{str(e)}")


def create_and_get_user_by_primary_wallet_address(
    db: Session, primary_wallet_address: str
):
    user = get_user_by_wallet_address(db, primary_wallet_address)
    if user:
        return user
    user = sign_up_new_user(
        db, primary_wallet_address, "__ergoauth_default", primary_wallet_address
    )
    return user


##################################


@r.post("/admin/token", name="auth:admin-login")
async def admin_login(
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

        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
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
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "permissions": permissions,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::login::{str(e)}")


@r.post("/admin/signup", name="auth:admin-signup")
async def admin_signup(
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

        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
        if user.is_superuser:
            permissions = "admin"
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin only endpoint - Your account is under review, contact the dev team for details",
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
async def logout(
    db=Depends(get_db),
    token: str = Depends(security.oauth2_scheme),
    current_user=Depends(get_current_active_user),
):
    try:
        return blacklist_token(db, token)
    except Exception as e:
        JSONResponse(status_code=400, content=f"ERR::logout::{str(e)}")
