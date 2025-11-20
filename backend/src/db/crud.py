

from sqlalchemy.orm import Session, selectinload

from src.api.v1 import schemas
from src.core.enums import AnalysisStatus
from src.db import models


def get_user_by_username(db: Session, username: str):
    """
    Retrieves a user from the database by their username.
    """
    return db.query(models.User).filter(models.User.username == username).first()


def get_repository_by_url(db: Session, url: str):
    """
    Retrieves a repository from the database by its URL.
    """
    return db.query(models.Repository).options(selectinload(models.Repository.analysis_results)).filter(models.Repository.url == str(url)).first()


def create_repository(db: Session, url: str, name: str, owner_id: int):
    """
    Creates a new repository record in the database.
    """
    db_repo = models.Repository(
        url=url,
        name=name,
        owner_id=owner_id,
        status=AnalysisStatus.PENDING
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo


def get_repositories(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of repositories from the database.
    """
    return db.query(models.Repository).options(selectinload(models.Repository.analysis_results)).offset(skip).limit(limit).all()


def get_repositories_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of repositories for a specific owner.
    """
    return db.query(models.Repository).filter(models.Repository.owner_id == owner_id).options(selectinload(models.Repository.analysis_results)).offset(skip).limit(limit).all()


def get_repository(db: Session, repository_id: int):
    """
    Retrieves a single repository from the database by its ID.
    """
    return db.query(models.Repository).options(selectinload(models.Repository.analysis_results)).filter(models.Repository.id == repository_id).first()


def get_analysis_results_for_repository(db: Session, repository_id: int):
    """
    Retrieves all analysis results for a given repository ID.
    """
    return db.query(models.AnalysisResult).filter(
        models.AnalysisResult.repository_id == repository_id
    ).all()



def create_analysis_result(db: Session, analysis: schemas.AnalysisResultCreate):
    """
    Creates a new analysis result record in the database from a schema object.
    """
    db_analysis_result = models.AnalysisResult(**analysis.model_dump())
    db_analysis_result.status = analysis.status # Explicitly set the status
    db_analysis_result.total_lines = analysis.total_lines # Explicitly set total_lines
    db_analysis_result.report_url = analysis.report_url # Explicitly set report_url
    db.add(db_analysis_result)
    db.commit()
    db.refresh(db_analysis_result)
    return db_analysis_result

def get_analysis_result(db: Session, analysis_id: int):
    """
    Retrieves a single analysis result from the database by its ID.
    """
    return db.query(models.AnalysisResult).filter(models.AnalysisResult.id == analysis_id).first()


def update_repository_status(db: Session, repository_id: int, new_status: AnalysisStatus):
    """
    Updates the status of a repository.
    """
    db_repo = db.query(models.Repository).filter(models.Repository.id == repository_id).first()
    if db_repo:
        db_repo.status = new_status
        db.commit()
        db.refresh(db_repo)
    return db_repo


def update_analysis_result_summary(db: Session, analysis_id: int, new_summary: str):
    """
    Updates the summary of an analysis result.
    """
    db_analysis_result = db.query(models.AnalysisResult).filter(models.AnalysisResult.id == analysis_id).first()
    if db_analysis_result:
        db_analysis_result.summary = new_summary
        db.commit()
        db.refresh(db_analysis_result)
    return db_analysis_result


def delete_repository(db: Session, repository_id: int):
    """
    Deletes a repository and its associated analysis results.
    """
    db_repo = db.query(models.Repository).filter(models.Repository.id == repository_id).first()
    if db_repo:
        db.delete(db_repo)
        db.commit()
    return db_repo


def delete_analysis_result(db: Session, analysis_id: int):
    """
    Deletes an analysis result.
    """
    db_analysis_result = db.query(models.AnalysisResult).filter(models.AnalysisResult.id == analysis_id).first()
    if db_analysis_result:
        db.delete(db_analysis_result)
        db.commit()
    return db_analysis_result
