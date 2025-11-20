import asyncio
import json
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.v1 import schemas
from src.api.v1.connection_manager import manager
from src.celery_app import celery_app
from src.core.enums import (
    AnalysisStatus,  # Import AnalysisStatus from the new common module
)
from src.db import crud, models
from src.db.database import SessionLocal

from .github_service import GitHubService  # Import GitHubService
from .narrative_generator import NarrativeGenerator  # Import NarrativeGenerator
from .repository_analyzer import RepositoryAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def _broadcast_status_update(repo_id: int, status: AnalysisStatus):
    """Helper function to broadcast repository status updates."""
    await manager.broadcast(json.dumps({"id": repo_id, "status": status.value}))

@celery_app.task
def clone_and_analyze_repository(repo_id: int, db: Session = None):
    """
    Analyzes a repository using GitHub API, generates a recruiter summary, and updates the database.
    This function runs as a Celery task.
    """
    close_db_session = False
    if db is None:
        db = SessionLocal()
        close_db_session = True

    repo = crud.get_repository(db, repo_id)
    if not repo:
        logging.warning(f"Repository with ID {repo_id} not found.")
        if close_db_session:
            db.close()
        return

    try:
        repo.status = AnalysisStatus.IN_PROGRESS
        db.commit()
        db.refresh(repo)
        asyncio.run(_broadcast_status_update(repo.id, repo.status))

        # Initialize services
        github_service = GitHubService() # Still need GitHubService for RepositoryAnalyzer
        repository_analyzer = RepositoryAnalyzer(github_service)

        # Perform repository analysis using the new method
        repo_analysis = asyncio.run(repository_analyzer.get_repository_analysis(repo.url))

        # Trigger asynchronous narrative generation
        generate_narratives_task.delay(repo.id, repo_analysis)

        # Extract relevant data for AnalysisResult
        file_count = repo_analysis.get("file_count", 0)
        commit_count = repo_analysis.get("commit_count", 0)
        languages = repo_analysis.get("languages", {})
        open_issues_count = repo_analysis.get("open_issues_count", 0)
        open_pull_requests_count = repo_analysis.get("open_pull_requests_count", 0)
        contributors = repo_analysis.get("contributors", [])
        tech_stack = repo_analysis.get("tech_stack", [])

        # Create AnalysisResult (summary and narrative will be updated by generate_narratives_task)
        analysis_data = schemas.AnalysisResultCreate(
            repository_id=repo.id,
            summary="Generating summary...", # Placeholder
            narrative="Generating narrative...", # Placeholder
            file_count=file_count,
            commit_count=commit_count,
            languages=languages,
            open_issues_count=open_issues_count,
            open_pull_requests_count=open_pull_requests_count,
            contributors=contributors,
            tech_stack=tech_stack,
            status=repo.status,
        )
        crud.create_analysis_result(db=db, analysis=analysis_data)

        repo.status = AnalysisStatus.COMPLETED
        logging.info(f"Repository {repo.name} analysis status set to COMPLETED.")
        asyncio.run(_broadcast_status_update(repo.id, repo.status))

    except Exception as e:
        repo.status = AnalysisStatus.FAILED
        repo.summary = f"An unexpected error occurred during analysis: {e}" # Include exception message
        logging.error(f"Error analyzing {repo.url}: {e}")
        asyncio.run(_broadcast_status_update(repo.id, repo.status))
    finally:
        repo.updated_at = func.now()
        db.add(repo)
        db.commit()
        db.refresh(repo)
        if close_db_session:
            db.close()
            logging.info("Closed DB session for task.")


@celery_app.task
def generate_narratives_task(repo_id: int, repo_analysis: dict, db: Session = None):
    """
    Generates narratives (comprehensive and recruiter summary) for a repository using an LLM
    and updates the AnalysisResult in the database.
    This function runs as a Celery task.
    """
    close_db_session = False
    if db is None:
        db = SessionLocal()
        close_db_session = True
    
    try:
        narrative_generator = NarrativeGenerator()

        # Update the AnalysisResult in the database
        analysis_result = db.query(models.AnalysisResult).filter(models.AnalysisResult.repository_id == repo_id).first()
        if analysis_result:
            # Generate comprehensive narrative
            comprehensive_narrative = narrative_generator.generate_narrative(repo_analysis)

            # Generate recruiter summary
            recruiter_summary = asyncio.run(narrative_generator.generate_recruiter_summary(repo_analysis))

            analysis_result.summary = recruiter_summary
            analysis_result.narrative = comprehensive_narrative # Assuming a 'narrative' field exists in AnalysisResult
            db.add(analysis_result)
            db.commit()
            db.refresh(analysis_result)
            logging.info(f"Narratives generated and updated for repository ID {repo_id}.")
        else:
            logging.warning(f"AnalysisResult not found for repository ID {repo_id}. Cannot update narratives.")

    except Exception as e:
        logging.error(f"Error generating narratives for repository ID {repo_id}: {e}")
    finally:
        if close_db_session:
            db.close()
            logging.info("Closed DB session for narrative generation task.")
