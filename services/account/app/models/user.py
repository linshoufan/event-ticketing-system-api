from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

VALID_ROLES = ("employee", "welfare_member", "hr")
VALID_REGISTRATION_STATUSES = ("active", "locked")
VALID_DIET_TYPES = ("veg", "non-veg")
VALID_TAGS = ("sport", "food", "travel", "culture", "family", "contest", "music")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('employee','welfare_member','hr')", name="check_user_role"),
        CheckConstraint("registration_status IN ('active','locked')", name="check_registration_status"),
        CheckConstraint("diet_type IN ('veg','non-veg')", name="check_diet_type"),
    )

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="employee")
    registration_status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    unlock_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    diet_type: Mapped[str | None] = mapped_column(String(10), nullable=True, default="non-veg")
    self_driving: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    interest_tags: Mapped[list["UserInterestTag"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[list["UserPreference"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserInterestTag(Base):
    __tablename__ = "user_interest_tags"
    __table_args__ = (
        UniqueConstraint("user_id", "tag"),
        CheckConstraint("tag IN ('sport','food','travel','culture','family','contest','music')", name="check_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(50), nullable=False)

    user: Mapped["User"] = relationship(back_populates="interest_tags")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "category"),
        CheckConstraint("diet_type IN ('veg','non-veg')", name="check_preference_diet_type"),
        CheckConstraint("category IN ('sport','food','travel','culture','family','contest','music')", name="check_preference_category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    diet_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    self_driving: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    guest_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="preferences")
