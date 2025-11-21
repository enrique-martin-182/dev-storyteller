from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.enums import (
    AnalysisStatus,  # Import AnalysisStatus from the new common module
)

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    repositories = relationship("Repository", back_populates="owner")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING)
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="repositories")
    analysis_results = relationship("AnalysisResult", back_populates="repository", cascade="all, delete-orphan")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    summary = Column(Text)
    narrative = Column(Text) # New field for comprehensive narrative
    open_issues_count = Column(Integer, default=0)
    open_pull_requests_count = Column(Integer, default=0)
    contributors = Column(JSON)
    file_count = Column(Integer)
    total_lines = Column(Integer)
    commit_count = Column(Integer)
    languages = Column(JSON)
    tech_stack = Column(JSON) # New field for identified technologies
    report_url = Column(String) # Add report_url column
    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING) # Add status column
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    repository = relationship("Repository", back_populates="analysis_results")
