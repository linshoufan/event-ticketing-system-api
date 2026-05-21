from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import role_required, self_or_role
from app.core.response import paginated, success
from app.models.user import User
from app.schemas.user import (
    AutofillSchema,
    CreateUserRequest,
    CreateUserResponse,
    DeletedResponse,
    UpdatedResponse,
    UpdateRoleRequest,
    UpdateUserRequest,
    UserListItemResponse,
    UserResponse,
)
from app.services import user_service

router = APIRouter()


@router.get("/users", response_model=dict)
def list_users(
    page: int = 1,
    limit: int = 20,
    role: str | None = None,
    status: str | None = None,
    current_user: User = Depends(role_required("welfare_member")),
    db: Session = Depends(get_db),
):
    users, total = user_service.list_users(db=db, page=page, limit=limit, role=role, status=status)
    data = [
        UserListItemResponse(
            userId=u.user_id,
            username=u.username,
            role=u.role,
            registrationStatus=u.registration_status,
            unlockAt=u.unlock_at,
        ).model_dump()
        for u in users
    ]
    return paginated(data=data, page=page, limit=limit, total=total)


@router.post("/users", response_model=dict, status_code=201)
def create_user(
    body: CreateUserRequest,
    current_user: User = Depends(role_required("welfare_member")),
    db: Session = Depends(get_db),
):
    user = user_service.create_user(data=body, db=db)
    return success(
        CreateUserResponse(
            userId=user.user_id,
            username=user.username,
            role=user.role,
        ).model_dump()
    )


@router.get("/users/{user_id}", response_model=dict)
def get_user(
    user_id: str,
    current_user: User = Depends(self_or_role("welfare_member")),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_id(user_id=user_id, db=db)
    return success(
        UserResponse(
            userId=user.user_id,
            username=user.username,
            role=user.role,
            preferences=[t.tag for t in user.interest_tags],
            registrationStatus=user.registration_status,
            unlockAt=user.unlock_at,
            autofill=AutofillSchema(
                dietType=user.diet_type,
                selfDriving=user.self_driving,
            ),
        ).model_dump()
    )


@router.patch("/users/{user_id}", response_model=dict)
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: User = Depends(self_or_role("welfare_member")),
    db: Session = Depends(get_db),
):
    user = user_service.update_user(user_id=user_id, data=body, db=db)
    return success(
        UpdatedResponse(updated=True, updatedAt=user.updated_at).model_dump()
    )


@router.patch("/users/{user_id}/role", response_model=dict)
def update_user_role(
    user_id: str,
    body: UpdateRoleRequest,
    current_user: User = Depends(role_required("welfare_member")),
    db: Session = Depends(get_db),
):
    user = user_service.update_user_role(
        user_id=user_id, role=body.role, current_user=current_user, db=db
    )
    return success(
        UpdatedResponse(updated=True, updatedAt=user.updated_at).model_dump()
    )


@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: str,
    current_user: User = Depends(role_required("welfare_member")),
    db: Session = Depends(get_db),
):
    user_service.delete_user(user_id=user_id, db=db)
    return success(DeletedResponse(deleted=True).model_dump())


@router.patch("/users/{user_id}/unlock", response_model=dict)
def unlock_user(
    user_id: str,
    current_user: User = Depends(role_required("welfare_member")),
    db: Session = Depends(get_db),
):
    user = user_service.unlock_user(user_id=user_id, db=db)
    return success(
        UpdatedResponse(updated=True, updatedAt=user.updated_at).model_dump()
    )
