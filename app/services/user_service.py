"""User profile service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import UserNotFoundException
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.user import UserUpdateRequest

log = get_logger(__name__)


class UserService:

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()
        return user

    @staticmethod
    def update_profile(db: Session, user_id: int, payload: UserUpdateRequest) -> User:
        user = UserService.get_by_id(db, user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        log.info(f"User {user_id} profile updated: {list(update_data.keys())}")
        return user

    @staticmethod
    def update_profile_image(db: Session, user_id: int, image_path: str) -> User:
        user = UserService.get_by_id(db, user_id)
        user.profile_image = image_path
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def deactivate(db: Session, user_id: int) -> None:
        user = UserService.get_by_id(db, user_id)

        db.delete(user)
        db.commit()

        log.info(f"User {user_id} permanently deleted.")