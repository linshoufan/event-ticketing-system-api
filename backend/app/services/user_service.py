import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserInterestTag
from app.schemas.user import CreateUserRequest, UpdateUserRequest


def get_user_by_id(user_id: str, db: Session) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )
    return user


def list_users(
    db: Session,
    page: int = 1,
    limit: int = 20,
    role: str | None = None,
    status: str | None = None,
) -> tuple[list[User], int]:
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.registration_status == status)
    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()
    return users, total


def create_user(data: CreateUserRequest, db: Session) -> User:
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "USERNAME_TAKEN", "message": "Username already exists"},
        )
    user = User(
        user_id=str(uuid.uuid4()),
        username=data.username,
        email=f"{data.username}@placeholder.com",
        role=data.role,
        registration_status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(user_id: str, data: UpdateUserRequest, db: Session) -> User:
    user = get_user_by_id(user_id, db)

    if data.autofill is not None:
        if data.autofill.dietType is not None:
            user.diet_type = data.autofill.dietType
        if data.autofill.selfDriving is not None:
            user.self_driving = data.autofill.selfDriving

    if data.preferences is not None:
        db.query(UserInterestTag).filter(UserInterestTag.user_id == user_id).delete()
        for tag in data.preferences:
            db.add(UserInterestTag(user_id=user_id, tag=tag))

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(user_id: str, role: str, current_user: User, db: Session) -> User:
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "CANNOT_MODIFY_OWN_ROLE", "message": "Cannot modify your own role"},
        )
    user = get_user_by_id(user_id, db)
    user.role = role
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def delete_user(user_id: str, db: Session) -> None:
    user = get_user_by_id(user_id, db)
    db.delete(user)
    db.commit()


def unlock_user(user_id: str, db: Session) -> User:
    user = get_user_by_id(user_id, db)
    if user.registration_status != "locked":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "USER_NOT_LOCKED", "message": "User is not locked"},
        )
    user.registration_status = "active"
    user.unlock_at = None
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def punish_user(user_id: str, db: Session) -> User:
    user = get_user_by_id(user_id, db)
    user.registration_status = "locked"
    user.unlock_at = datetime.now(timezone.utc) + timedelta(days=30)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
