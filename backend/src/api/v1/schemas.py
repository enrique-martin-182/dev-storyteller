from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from src.core.enums import AnalysisStatus

# ========== Base Schemas ==========

class RepositoryBase(BaseModel):
    url: HttpUrl


class AnalysisResultBase(BaseModel):
    summary: str | None = None
    narrative: str | None = None
    file_count: int | None = None
    commit_count: int | None = None
    languages: dict | None = None
    open_issues_count: int | None = None
    open_pull_requests_count: int | None = None
    contributors: list[dict] | None = None
    tech_stack: list[str] | None = None
    status: AnalysisStatus
    total_lines: int | None = None
    report_url: str | None = None


# ========== Create Schemas ==========

class RepositoryCreate(RepositoryBase):
    pass


class AnalysisResultCreate(AnalysisResultBase):
    repository_id: int


# ========== Read Schemas ==========

class AnalysisResult(AnalysisResultBase):
    id: int
    repository_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Repository(BaseModel):
    id: int
    name: str
    url: HttpUrl # Added url field
    owner_id: int # Add owner_id
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime | None = None
    analysis_results: list[AnalysisResult] = []

    model_config = ConfigDict(from_attributes=True)

class AnalysisResultsList(BaseModel):
    analysis_results: list[AnalysisResult]

# Manually rebuild the models to resolve forward references
# This is often needed in complex applications with circular dependencies
Repository.model_rebuild()
AnalysisResult.model_rebuild()
AnalysisResultsList.model_rebuild()
