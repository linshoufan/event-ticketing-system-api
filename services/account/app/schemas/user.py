from datetime import datetime

from pydantic import BaseModel


# GET /auth/login
class LoginResponse(BaseModel):
    loginUrl: str


# GET /auth/callback
class CallbackResponse(BaseModel):
    token: str
    role: str


# 共用：autofill 欄位結構
class AutofillSchema(BaseModel):
    dietType: str | None = None
    selfDriving: bool | None = None


# GET /me, GET /users/{userId}
class UserResponse(BaseModel):
    userId: str
    username: str
    role: str
    preferences: list[str] = []
    registrationStatus: str
    unlockAt: datetime | None = None
    autofill: AutofillSchema


# GET /users（列表單筆）
class UserListItemResponse(BaseModel):
    userId: str
    username: str
    role: str
    registrationStatus: str
    unlockAt: datetime | None = None


# POST /users request
class CreateUserRequest(BaseModel):
    username: str
    role: str


# POST /users response
class CreateUserResponse(BaseModel):
    userId: str
    username: str
    role: str


# PATCH /users/{userId} request
class UpdateUserRequest(BaseModel):
    preferences: list[str] | None = None
    autofill: AutofillSchema | None = None


# PATCH /users/{userId}/role request
class UpdateRoleRequest(BaseModel):
    role: str


# PATCH /users/{userId}, PATCH /users/{userId}/role, PATCH /users/{userId}/unlock response
class UpdatedResponse(BaseModel):
    updated: bool
    updatedAt: datetime


# DELETE /users/{userId} response
class DeletedResponse(BaseModel):
    deleted: bool
