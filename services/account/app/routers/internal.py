from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import verify_internal_key
from app.core.response import success
from app.schemas.user import AutofillSchema
from app.services import user_service

router = APIRouter()


@router.get("/internal/users/{user_id}/registration-profile", response_model=dict)
def get_registration_profile(
    user_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_key),
):
    user = user_service.get_user_by_id(user_id=user_id, db=db)
    return success({
        "userId": user.user_id,
        "role": user.role,
        "registrationStatus": user.registration_status,
        "unlockAt": user.unlock_at.isoformat() if user.unlock_at else None,
        "autofill": AutofillSchema(
            dietType=user.diet_type,
            selfDriving=user.self_driving,
        ).model_dump(),
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
        "unlockAt": user.unlock_at.isoformat() if user.unlock_at else None,
    })
