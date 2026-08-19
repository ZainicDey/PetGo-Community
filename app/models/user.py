from typing import Optional
from datetime import datetime, date
import uuid as uuid_pkg
from uuid import UUID as PyUUID
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class DjangoUser(Base):
    __tablename__ = "auth_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    userinfo: Mapped[Optional["DjangoUserModel"]] = relationship("DjangoUserModel", back_populates="user", uselist=False)
    social_profile: Mapped[Optional["SocialProfile"]] = relationship("SocialProfile", back_populates="user", uselist=False)

class DjangoUserModel(Base):
    __tablename__ = "user_usermodel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), default=uuid_pkg.uuid4, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_user.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["DjangoUser"] = relationship("DjangoUser", back_populates="userinfo")

class SocialProfile(Base):
    __tablename__ = "social_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_user.id", ondelete="CASCADE"), unique=True, nullable=False)
    profile_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'pet' or 'user'
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user: Mapped["DjangoUser"] = relationship("DjangoUser", back_populates="social_profile")
