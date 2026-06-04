from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import verify_internal_key
from app.core.response import success
from app.schemas.user import AutofillUpdateRequest
from app.services import user_service

router = APIRouter()

def isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


@router.get("/internal/users/{user_id}/registration-profile", response_model=dict)
def get_registration_profile(
    user_id: str,
    category: str | None = None, 
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_key),
):
    user = user_service.get_user_by_id(user_id=user_id, db=db)
    autofill = user_service.resolve_autofill(user=user, category=category, db=db) 
    return success({
        "userId": user.user_id,
        "username": user.username,
        "role": user.role,
        "registrationStatus": user.registration_status,
        "unlockAt": isoformat_utc(user.unlock_at),
        "autofill": autofill,
        "preferences": [t.tag for t in user.interest_tags],
    })


@router.post("/internal/users/{user_id}/punish", response_model=dict)
def punish_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_key),
):
    user = user_service.punish_user(user_id=user_id, db=db)
    return success({
        "userId": user.user_id,
        "registrationStatus": user.registration_status,
        "unlockAt": isoformat_utc(user.unlock_at),
    })

@router.patch("/internal/users/{user_id}/autofill", response_model=dict)
def update_autofill(
    user_id: str,
    body: AutofillUpdateRequest, 
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_key),
):
    user_service.upsert_autofill(
        user_id=user_id,
        category=body.category,
        diet_type=body.dietType,
        self_driving=body.selfDriving,
        guest_count=body.guestCount,
        db=db,
    )
    return success({"updated": True})