import typing as t
from fastapi import APIRouter, Depends, Response, status
from starlette.responses import JSONResponse
from db.session import get_db
from db.crud.users import (
    get_users,
    get_user,
    create_user,
    delete_user,
    edit_user,
    get_user_profile,
    get_user_profile_settings,
    edit_user_profile,
    edit_user_profile_settings,
    update_user_follower
)
from db.schemas.users import UserCreate, UserEdit, User, UserDetails, UserProfileSettings, UpdateUserDetails, UpdateUserProfileSettings, FollowUserRequest
from core.auth import get_current_active_user, get_current_active_superuser

users_router = r = APIRouter()


@r.get(
    "/",
    response_model=t.List[User],
    response_model_exclude_none=True,
    name="users:all-users"
)
async def users_list(
    response: Response,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


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
    name="users:user"
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/{user_id}", response_model=User, response_model_exclude_none=True, name="users:edit"
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.delete(
    "/{user_id}", response_model=User, response_model_exclude_none=True, name="users:delete"
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
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


##################
## USER PROFILE ##
##################


@r.get(
    "/details/{user_id}",
    response_model=UserDetails,
    response_model_exclude_none=True,
    name="users:user-details"
)
def user_details_all(
    user_id: int,
    db=Depends(get_db),
):
    """
    Get any user details
    """
    try:
        return get_user_profile(db, user_id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.get(
    "/profile/settings",
    response_model=UserProfileSettings,
    response_model_exclude_none=True,
    name="users:user-profile-settings"
)
def user_profile_settings(
    db=Depends(get_db),
    user=Depends(get_current_active_user),
):
    """
    Get any user profile preferences
    """
    try:
        return get_user_profile_settings(db, user.id)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/details/{user_id}", response_model=UserDetails, response_model_exclude_none=True, name="users:edit-details"
)
def edit_user_details(
    user_id: int,
    user_details: UpdateUserDetails,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing user details
    """
    try:
        if user_id != current_user.id:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="User not authorized")
        return edit_user_profile(db, user_id, user_details)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/profile/settings", response_model=UserProfileSettings, response_model_exclude_none=True, name="users:edit-profile-settings"
)
def edit_user_settings(
    user_settings: UpdateUserProfileSettings,
    db=Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update existing user preferences
    """
    try:
        return edit_user_profile_settings(db, current_user.id, user_settings)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')


@r.put(
    "/profile/follow", response_model_exclude_none=True, name="users:edit-profile-follow"
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
        return update_user_follower(db, current_user.id, req)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'{str(e)}')
