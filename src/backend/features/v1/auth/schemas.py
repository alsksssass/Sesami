from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    github_id: str
    username: str
    nickname: str
    repo_count: int
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GitHubCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class GitHubLoginResponse(BaseModel):
    authorization_url: str
