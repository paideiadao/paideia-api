from datetime import timedelta
import typing as t
from fastapi import APIRouter, Depends, Response, status
from starlette.responses import JSONResponse
from ergo_python_appkit.appkit import ErgoAppKit

from db.session import get_db
from db.crud.users import (
    get_users,
    get_user,
    search_users,
    create_user,
    delete_user,
    edit_user,
    get_user_address_config,
    get_user_profile,
    get_user_profile_settings,
    create_user_dao_profile,
    edit_user_profile,
    edit_user_profile_settings,
    update_user_follower,
    update_primary_address_for_user,
    get_dao_users,
    get_user_details_by_id,
)
from db.schemas.users import (
    UserCreate,
    UserEdit,
    User,
    UserDetails,
    UserProfileSettings,
    UpdateUserDetails,
    UpdateUserProfileSettings,
    FollowUserRequest,
    UserAddressConfig,
    PrimaryAddressChangeRequest,
)
from db.schemas.ergoauth import LoginRequestWebResponse, ErgoAuthResponse

from core.auth import get_current_active_user, get_current_active_superuser
from core.security import generate_signing_message, generate_verification_id
from cache.cache import cache
from core import security


users_router = r = APIRouter()


BASE_URL = "https://api.paideia.im"


@r.get(
    "/",
    response_model=t.List[User],
    response_model_exclude_none=True,
    name="users:all-users",
)
async def users_list(
    response: Response,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get all users
    """
    try:
        users = get_users(db)
        # This is necessary for react-admin to work
        response.headers["Content-Range"] = f"0-9/{len(users)}"
        return users
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get("/me", response_model=User, response_model_exclude_none=True, name="users:me")
async def user_me(current_user=Depends(get_current_active_user)):
    """
    Get own user
    """
    return current_user


@r.get(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
    name="users:user",
)
async def user_details(
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get any user details
    """
    try:
        return get_user(db, user_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post("/", response_model=User, response_model_exclude_none=True, name="users:create")
async def user_create(
    user: UserCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Create a new user
    """
    try:
        return create_user(db, user)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.put(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
    name="users:edit",
)
async def user_edit(
    user_id: int,
    user: UserEdit,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Update existing user
    """
    try:
        return edit_user(db, user_id, user)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.delete(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
    name="users:delete",
)
async def user_delete(
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Delete existing user
    """
    try:
        return delete_user(db, user_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


####################
## USER ADDRESSES ##
####################


@r.get(
    "/address_config/{user_id}",
    response_model=UserAddressConfig,
    response_model_exclude_none=True,
    name="user:user-address-config",
)
def user_address_config(
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get address config for user
    """
    try:
        if user_id == current_user.id:
            return get_user_address_config(db, user_id)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content="not authorized to read"
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post(
    "/change_primary_address",
    response_model=LoginRequestWebResponse,
    name="user:edit-user-address-config",
)
def edit_user_address_config(
    req: PrimaryAddressChangeRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Change primary address for user
    """
    try:
        verificationId = generate_verification_id()
        tokenUrl = f"{BASE_URL}/users/verify_address/{verificationId}"
        ret = {
            "user_id": current_user.id,
            "address": req.address,
            "signingMessage": generate_signing_message(),
            "tokenUrl": tokenUrl,
        }
        cache.set(f"ergoauth_primary_address_change_request_{verificationId}", ret)
        return ret
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post(
    "/verify_address/{request_id}",
    response_model=UserAddressConfig,
    name="user:verify-user-address-change",
)
def verify_user_address_change(
    request_id: str,
    authResponse: ErgoAuthResponse,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Change primary address for user (verification)
    """
    try:
        signingRequest = cache.get(
            f"ergoauth_primary_address_change_request_{request_id}"
        )
        if signingRequest["user_id"] != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )

        verified = ErgoAppKit.verifyErgoAuthSignedMessage(
            signingRequest["address"],
            signingRequest["signingMessage"],
            authResponse.signedMessage,
            authResponse.proof,
        )
        if verified:
            cache.invalidate(f"ergoauth_primary_address_change_request_{request_id}")
            permissions = "user"
            access_token_expires = timedelta(
                minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            access_token = security.create_access_token(
                data={"sub": signingRequest["address"], "permissions": permissions},
                expires_delta=access_token_expires,
            )
            ret = update_primary_address_for_user(
                db, current_user.id, signingRequest["address"]
            )
            return UserAddressConfig(
                id=ret.id,
                alias=ret.alias,
                addresses=ret.registered_addresses,
                access_token=access_token,
            )
        else:
            JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


##################
## USER PROFILE ##
##################


@r.get("/details/search", name="users:user-search")
def user_search(
    search_string: str,
    db=Depends(get_db),
):
    """
    Search for users
    """
    try:
        return search_users(db, search_string)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/by_dao_id/{dao_id}",
    response_model=t.List[UserDetails],
    response_model_exclude_none=True,
    name="users:user-dao-details",
)
def user_dao_details(
    dao_id: int,
    db=Depends(get_db),
):
    """
    Get users by dao
    """
    try:
        return get_dao_users(db, dao_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/details/{user_id}",
    response_model=UserDetails,
    response_model_exclude_none=True,
    name="users:user-details",
)
def user_details_all(
    user_id: int,
    dao_id: int,
    mapping: str = "user_id",
    db=Depends(get_db),
):
    """
    Get any user details
    """
    try:
        if mapping == "user_details_id":
            user_details = get_user_details_by_id(db, user_id)
            if type(user_details) == JSONResponse:
                return user_details
            return get_user_profile(db, user_details.user_id, user_details.dao_id)
        else:
            return get_user_profile(db, user_id, dao_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.get(
    "/profile/settings",
    response_model=UserProfileSettings,
    response_model_exclude_none=True,
    name="users:user-profile-settings",
)
def user_profile_settings(
    user_details_id: int,
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    """
    Get any user profile preferences
    """
    try:
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        return get_user_profile_settings(db, user_details_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.post(
    "/create_user_profile",
    response_model=UserDetails,
    response_model_exclude_none=True,
    name="users:create-details",
)
def create_user_profile(
    dao_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create new dao specific user profile
    """
    try:
        return create_user_dao_profile(db, current_user.id, dao_id)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.put(
    "/details/{user_details_id}",
    response_model=UserDetails,
    response_model_exclude_none=True,
    name="users:edit-details",
)
def edit_user_details(
    user_details_id: int,
    user_details: UpdateUserDetails,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing user details
    """
    try:
        _user_details = get_user_details_by_id(db, user_details_id)
        if type(_user_details) == JSONResponse:
            return _user_details
        if _user_details.user_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        return edit_user_profile(db, user_details_id, user_details)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.put(
    "/profile/settings",
    response_model=UserProfileSettings,
    response_model_exclude_none=True,
    name="users:edit-profile-settings",
)
def edit_user_settings(
    user_details_id: int,
    user_settings: UpdateUserProfileSettings,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing user preferences
    """
    try:
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        return edit_user_profile_settings(db, user_details_id, user_settings)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )


@r.put(
    "/profile/follow",
    response_model_exclude_none=True,
    name="users:edit-profile-follow",
)
def user_profile_follow(
    req: FollowUserRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Follow/Unfollow user
    """
    try:
        user_details_id = req.current_user_details_id
        user_details = get_user_details_by_id(db, user_details_id)
        if type(user_details) == JSONResponse:
            return user_details
        if user_details.user_id != current_user.id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content="user not authorized"
            )
        return update_user_follower(db, user_details_id, req)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=f"{str(e)}"
        )
