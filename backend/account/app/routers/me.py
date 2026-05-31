from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.response import success
from app.models.user import User
from app.schemas.user import AutofillSchema, UserResponse

router = APIRouter()


@router.get("/me", response_model=dict)
def get_me(current_user: User = Depends(get_current_user)):
    return success(
        UserResponse(
            userId=current_user.user_id,
            username=current_user.username,
            role=current_user.role,
            preferences=[t.tag for t in current_user.interest_tags],
            registrationStatus=current_user.registration_status,
            unlockAt=current_user.unlock_at,
            autofill=AutofillSchema(
                dietType=current_user.diet_type,
                selfDriving=current_user.self_driving,
            ),
        ).model_dump()
    )
