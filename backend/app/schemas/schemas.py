from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from enum import Enum


# ─── Auth ───────────────────────────────────────────────────

class OTPSendRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+\d{10,15}$")


class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    is_new: bool


# ─── User ───────────────────────────────────────────────────

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    phone: str
    name: Optional[str]
    email: Optional[str]
    role: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Freelancer ─────────────────────────────────────────────

class FreelancerProfileCreate(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    portfolio_links: Optional[list[str]] = Field(default=None, max_length=3)
    interest_areas: Optional[list[str]] = None
    availability: Optional[bool] = True


class FreelancerProfileUpdate(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    portfolio_links: Optional[list[str]] = None
    interest_areas: Optional[list[str]] = None
    availability: Optional[bool] = None
    profile_photo_url: Optional[str] = None


class FreelancerProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    headline: Optional[str]
    summary: Optional[str]
    location: Optional[str]
    skills: Optional[list[str]]
    interest_areas: Optional[list[str]]
    portfolio_links: Optional[list[str]]
    availability: Optional[bool]
    profile_photo_url: Optional[str]
    experience: Optional[list]
    education: Optional[list]
    avg_rating: Optional[float]
    completed_count: Optional[int]

    class Config:
        from_attributes = True


# ─── Client ─────────────────────────────────────────────────

class ClientProfileCreate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    about: Optional[str] = None
    website: Optional[str] = None


class ClientProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    about: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None


class ClientProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    company_name: Optional[str]
    industry: Optional[str]
    about: Optional[str]
    logo_url: Optional[str]
    website: Optional[str]

    class Config:
        from_attributes = True


# ─── Project ────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    timeline_value: Optional[int] = None
    timeline_unit: Optional[str] = None
    written_brief: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    budget: Optional[float] = None
    timeline_value: Optional[int] = None
    timeline_unit: Optional[str] = None
    written_brief: Optional[str] = None


class ProjectOut(BaseModel):
    id: UUID
    client_id: UUID
    title: str
    description: Optional[str]
    category: Optional[str]
    budget: Optional[float]
    timeline_value: Optional[int]
    timeline_unit: Optional[str]
    deadline: Optional[date]
    status: str
    assigned_freelancer_id: Optional[UUID]
    revision_count: Optional[int]
    created_at: Optional[datetime]
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Swipe ──────────────────────────────────────────────────

class SwipeRequest(BaseModel):
    project_id: str
    freelancer_id: str
    direction: str  # "left" or "right"


class SwipeBatchOut(BaseModel):
    profiles: list[FreelancerProfileOut]
    remaining: int


# ─── Payment ────────────────────────────────────────────────

class PaymentOut(BaseModel):
    id: UUID
    project_id: UUID
    type: str
    gross_amount: float
    net_amount: float
    status: str
    razorpay_order_id: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Rating ─────────────────────────────────────────────────

class RatingCreate(BaseModel):
    project_id: str
    ratee_id: str
    score: int = Field(..., ge=1, le=5)
    review: Optional[str] = None


class RatingOut(BaseModel):
    id: UUID
    project_id: UUID
    rater_id: UUID
    ratee_id: UUID
    score: int
    review: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Revision ───────────────────────────────────────────────

class RevisionRequestCreate(BaseModel):
    note: str


# ─── Notification ───────────────────────────────────────────

class NotificationOut(BaseModel):
    id: UUID
    type: Optional[str]
    title: Optional[str]
    body: Optional[str]
    data: Optional[dict]
    read: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
