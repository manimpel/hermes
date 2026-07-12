import uuid
from datetime import datetime, date, timedelta, time
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Enum as SAEnum, DECIMAL, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ─── Enums ──────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    FREELANCER = "freelancer"
    CLIENT = "client"
    BOTH = "both"


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    MATCHING = "MATCHING"
    ADVANCE_PENDING = "ADVANCE_PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    NEAR_COMPLETION_REQUESTED = "NEAR_COMPLETION_REQUESTED"
    NEAR_COMPLETION_APPROVED = "NEAR_COMPLETION_APPROVED"
    NEAR_COMPLETION_REJECTED = "NEAR_COMPLETION_REJECTED"
    COMPLETED_REQUESTED = "COMPLETED_REQUESTED"
    REVISION_1 = "REVISION_1"
    REVISION_2 = "REVISION_2"
    REVISION_3 = "REVISION_3"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    DISPUTED = "DISPUTED"


class TimelineUnit(str, enum.Enum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


class SwipeDirection(str, enum.Enum):
    LEFT = "left"
    RIGHT = "right"


class PaymentType(str, enum.Enum):
    ADVANCE = "ADVANCE"
    FINAL = "FINAL"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


# ─── Models ─────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(15), unique=True, nullable=False)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    role = Column(SAEnum(UserRole), nullable=True)
    fcm_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    freelancer_profile = relationship("FreelancerProfile", back_populates="user", uselist=False)
    client_profile = relationship("ClientProfile", back_populates="user", uselist=False)


class FreelancerProfile(Base):
    __tablename__ = "freelancer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    linkedin_raw_html = Column(Text, nullable=True)
    linkedin_parsed = Column(JSONB, nullable=True)
    portfolio_links = Column(ARRAY(Text), default=list)
    interest_areas = Column(ARRAY(Text), default=list)
    availability = Column(Boolean, default=True)
    current_project_id = Column(UUID(as_uuid=True), nullable=True)
    profile_photo_url = Column(Text, nullable=True)
    headline = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    experience = Column(JSONB, default=list)
    skills = Column(ARRAY(Text), default=list)
    education = Column(JSONB, default=list)
    location = Column(Text, nullable=True)
    avg_rating = Column(DECIMAL(3, 2), nullable=True)
    completed_count = Column(Integer, default=0)

    user = relationship("User", back_populates="freelancer_profile")


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    about = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    website = Column(Text, nullable=True)

    user = relationship("User", back_populates="client_profile")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    budget = Column(DECIMAL(12, 2), nullable=True)
    timeline_value = Column(Integer, nullable=True)
    timeline_unit = Column(SAEnum(TimelineUnit), nullable=True)
    deadline = Column(Date, nullable=True)
    work_samples = Column(ARRAY(Text), default=list)
    audio_brief_url = Column(Text, nullable=True)
    written_brief = Column(Text, nullable=True)
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    assigned_freelancer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    revision_count = Column(Integer, default=0)
    revision_window_expires = Column(DateTime, nullable=True)
    advance_payment_id = Column(UUID(as_uuid=True), nullable=True)
    final_payment_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    client = relationship("User", foreign_keys=[client_id])
    assigned_freelancer = relationship("User", foreign_keys=[assigned_freelancer_id])


class DailyMatchBatch(Base):
    __tablename__ = "daily_match_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    batch_date = Column(Date, nullable=False)
    freelancer_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    swiped_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    selected_freelancer_id = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime, nullable=True)


class Swipe(Base):
    __tablename__ = "swipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    freelancer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    direction = Column(SAEnum(SwipeDirection), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    type = Column(SAEnum(PaymentType), nullable=False)
    gross_amount = Column(DECIMAL(12, 2), nullable=False)
    platform_fee = Column(DECIMAL(12, 2), default=0)
    net_amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING)
    razorpay_order_id = Column(Text, nullable=True)
    razorpay_payment_id = Column(Text, nullable=True)
    razorpay_payout_id = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)


class RevisionRequest(Base):
    __tablename__ = "revision_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    request_number = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    rater_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ratee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    data = Column(JSONB, default=dict)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FreelancerBankDetails(Base):
    __tablename__ = "freelancer_bank_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    account_number = Column(String(30), nullable=True)
    ifsc_code = Column(String(11), nullable=True)
    upi_id = Column(String(100), nullable=True)
    razorpay_fund_account_id = Column(Text, nullable=True)
    razorpay_contact_id = Column(Text, nullable=True)
