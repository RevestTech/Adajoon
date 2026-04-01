from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)

    channels = relationship("Channel", back_populates="category")


class Language(Base):
    __tablename__ = "languages"

    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)


class Country(Base):
    __tablename__ = "countries"

    code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    flag = Column(String(10), default="")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    alt_names = Column(Text, default="")
    network = Column(String(500), default="")
    country_code = Column(String(10), ForeignKey("countries.code"), default="", index=True)
    subdivision = Column(String(100), default="")
    city = Column(String(255), default="")
    categories = Column(String(500), default="")
    category_id = Column(String, ForeignKey("categories.id"), nullable=True, index=True)
    is_nsfw = Column(Boolean, default=False)
    launched = Column(String(50), default="")
    closed = Column(String(50), default="")
    website = Column(Text, default="")
    logo = Column(Text, default="")
    stream_url = Column(Text, default="")
    languages = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    updated_at = Column(String(50), default="")
    health_status = Column(String(20), default="unknown")
    health_checked_at = Column(String(50), default="")

    category = relationship("Category", back_populates="channels")

    __table_args__ = (
        Index("ix_channels_name_trgm", "name"),
    )


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"), index=True)
    url = Column(Text, nullable=False)
    http_referrer = Column(Text, default="")
    user_agent = Column(Text, default="")
    status = Column(String(50), default="unknown")
    added_at = Column(String(50), default="")
