from pydantic import BaseModel


class LoginResponse(BaseModel):
    loginUrl: str


class CallbackResponse(BaseModel):
    token: str
    role: str
