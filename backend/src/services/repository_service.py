import re

from sqlalchemy.orm import Session

from src.api.v1 import schemas
from src.db import crud as default_crud
from src.services import analysis_service as default_analysis_service


class RepositoryService:
    def __init__(self, crud_module=default_crud, analysis_service_module=default_analysis_service):
        self.crud = crud_module
        self.analysis_service = analysis_service_module

    def extract_repo_name_from_url(self, url: str) -> str:
        """
        Extracts the 'owner/repo_name' from a GitHub repository URL.
        Assumes URLs are in the format https://github.com/owner/repo_name(.git)
        """
        match = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?$", url)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid GitHub URL format: {url}")

    def get_repository_by_url(self, db: Session, url: str):
        return self.crud.get_repository_by_url(db, url)

    def create_repository(self, db: Session, repo: schemas.RepositoryCreate, owner_id: int):
        repo_name = self.extract_repo_name_from_url(str(repo.url))
        db_repo = self.crud.create_repository(db=db, url=str(repo.url), name=repo_name, owner_id=owner_id)
        # Trigger the analysis service asynchronously
        self.analysis_service.clone_and_analyze_repository.delay(db_repo.id)
        return db_repo

    def get_repositories_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100):
        return self.crud.get_repositories_by_owner(db, owner_id=owner_id, skip=skip, limit=limit)

    def get_repository(self, db: Session, repository_id: int):
        return self.crud.get_repository(db, repository_id)

    def get_analysis_results_for_repository(self, db: Session, repository_id: int):
        return self.crud.get_analysis_results_for_repository(db, repository_id)

    def get_analysis_narrative(self, db: Session, analysis_id: int):
        analysis_result = self.crud.get_analysis_result(db, analysis_id)
        if analysis_result:
            return analysis_result.narrative
        return None

# Instantiate a default service
repository_service = RepositoryService()