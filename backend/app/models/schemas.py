from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ===== User Schemas =====
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# ===== Trial Schemas =====
class TrialBase(BaseModel):
    title: str


class TrialCreate(TrialBase):
    pass


class TrialResponse(TrialBase):
    id: int
    protocol_file_path: Optional[str]
    original_filename: Optional[str]
    status: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== Generated Content Schemas =====
class GeneratedContentBase(BaseModel):
    content_type: str
    content_text: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None


class GeneratedContentCreate(GeneratedContentBase):
    trial_id: int


class GeneratedContentResponse(GeneratedContentBase):
    id: int
    trial_id: int
    is_approved: bool
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrialWithContent(TrialResponse):
    generated_content: List[GeneratedContentResponse] = []
    
    class Config:
        from_attributes = True
