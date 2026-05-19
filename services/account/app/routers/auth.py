from fastapi import APIRouter

router = APIRouter()


@router.get("/auth/login")
def login_placeholder():
    return {"message": "Placeholder for login API"}
