from sqlalchemy import String,Integer,DateTime,func,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column

from datetime import datetime

from .db import Base

class Otp_store(Base):
    __tablename__ = "otpstorage"

    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    email:Mapped[str] = mapped_column(String(255),unique=True,index=True)
    otp:Mapped[str] = mapped_column(String(5))
    expires_at:Mapped[datetime] = mapped_column(DateTime)


class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    username:Mapped[str] = mapped_column(String(255))
    email:Mapped[str] = mapped_column(String(255),unique=True,index=True)
    hashed_password:Mapped[str] = mapped_column(String(255))
    created_at:Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now()
    )


class Documnet(Base):
    __tablename__ = "document"

    id:Mapped[int] =mapped_column(primary_key=True)
    user_id:Mapped[int] = mapped_column(ForeignKey("users.id"),index=True)
    filename:Mapped[str] = mapped_column(String(512))
    file_hash:Mapped[str] = mapped_column(String(64),index=True)
    path:Mapped[str] = mapped_column(String(1024))
    pages:Mapped[int] = mapped_column(Integer,default=0,server_default="0")
    status:Mapped[str] = mapped_column(String(32),default="ready",server_default="ready")
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())