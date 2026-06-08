"""
User profile endpoints.

GET    /users/me               → Get current user profile
PUT    /users/me               → Update profile (name, language, settings)
POST   /users/me/profile-image → Upload profile picture
DELETE /users/me               → Deactivate account
"""
from __future__ import annotations

import os
import sys
if "app" not in sys.modules:
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

from fastapi import APIRouter, Depends, Request, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.file_utils import get_image_url, validate_and_save_image

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get my profile",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return SuccessResponse(
        message="Profile retrieved.",
        data=UserResponse.model_validate(current_user),
    )


@router.put(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Update my profile",
    description="Update name, language preference, dark mode, and notification settings.",
)
def update_my_profile(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = UserService.update_profile(db, current_user.id, payload)
    return SuccessResponse(
        message="Profile updated.",
        data=UserResponse.model_validate(updated),
    )


@router.post(
    "/me/profile-image",
    response_model=SuccessResponse[dict],
    summary="Upload profile picture",
)
async def upload_profile_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    relative_path, _ = await validate_and_save_image(file, sub_dir="profiles")
    UserService.update_profile_image(db, current_user.id, relative_path)
    base_url = str(request.base_url).rstrip("/")
    image_url = get_image_url(relative_path, base_url)
    return SuccessResponse(
        message="Profile image updated.",
        data={"image_url": image_url},
    )


@router.delete(
    "/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate account",
)
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    UserService.deactivate(db, current_user.id)
    return SuccessResponse(message="Account deactivated.")