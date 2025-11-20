import pytest
from sqlalchemy.orm import Session

from src.db import crud, models
from src.api.v1 import schemas
from src.core.enums import AnalysisStatus

def test_get_user_by_username(db_session: Session):
    # Create a user to test with
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Test that we can retrieve the user
    retrieved_user = crud.get_user_by_username(db_session, "testuser")
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"

    # Test that a non-existent user is not found
    retrieved_user = crud.get_user_by_username(db_session, "nonexistentuser")
    assert retrieved_user is None


def test_create_and_get_repository(db_session: Session):
    # Create a user to be the owner of the repository
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create a repository
    repo_url = "https://github.com/test/repo"
    repo_name = "test/repo"
    created_repo = crud.create_repository(db_session, url=repo_url, name=repo_name, owner_id=user.id)
    assert created_repo is not None
    assert created_repo.url == repo_url
    assert created_repo.name == repo_name
    assert created_repo.owner_id == user.id

    # Retrieve the repository by URL
    retrieved_repo = crud.get_repository_by_url(db_session, url=repo_url)
    assert retrieved_repo is not None
    assert retrieved_repo.id == created_repo.id
    assert retrieved_repo.name == repo_name

    # Retrieve the repository by ID
    retrieved_repo_by_id = crud.get_repository(db_session, repository_id=created_repo.id)
    assert retrieved_repo_by_id is not None
    assert retrieved_repo_by_id.id == created_repo.id
    assert retrieved_repo_by_id.name == repo_name


def test_get_repositories(db_session: Session):
    # Create a user and some repositories
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    crud.create_repository(db_session, url="https://github.com/test/repo1", name="test/repo1", owner_id=user.id)
    crud.create_repository(db_session, url="https://github.com/test/repo2", name="test/repo2", owner_id=user.id)

    repositories = crud.get_repositories(db_session)
    assert len(repositories) == 2


def test_get_repositories_by_owner(db_session: Session):
    # Create two users and some repositories
    user1 = models.User(username="testuser1", hashed_password="testpassword")
    user2 = models.User(username="testuser2", hashed_password="testpassword")
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    crud.create_repository(db_session, url="https://github.com/test/repo1", name="test/repo1", owner_id=user1.id)
    crud.create_repository(db_session, url="https://github.com/test/repo2", name="test/repo2", owner_id=user2.id)

    repositories = crud.get_repositories_by_owner(db_session, owner_id=user1.id)
    assert len(repositories) == 1
    assert repositories[0].owner_id == user1.id


def test_create_and_get_analysis_result(db_session: Session):
    # Create a user and a repository
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    repo = crud.create_repository(db_session, url="https://github.com/test/repo", name="test/repo", owner_id=user.id)

    # Create an analysis result
    analysis_create = schemas.AnalysisResultCreate(
        repository_id=repo.id,
        status=AnalysisStatus.PENDING,
        summary="Test Summary",
        narrative="Test Narrative",
        file_count=10,
        commit_count=5,
        total_lines=100,
        languages={"Python": 100},
        open_issues_count=1,
        open_pull_requests_count=2,
        contributors=[{"name": "test"}],
        tech_stack=["test"],
        report_url="http://test.com"
    )
    created_analysis = crud.create_analysis_result(db_session, analysis=analysis_create)
    assert created_analysis is not None
    assert created_analysis.repository_id == repo.id
    assert created_analysis.summary == "Test Summary"

    # Retrieve the analysis result
    retrieved_analysis = crud.get_analysis_result(db_session, analysis_id=created_analysis.id)
    assert retrieved_analysis is not None
    assert retrieved_analysis.id == created_analysis.id
    assert retrieved_analysis.summary == "Test Summary"

def test_get_analysis_results_for_repository(db_session: Session):
    # Create a user and a repository
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    repo = crud.create_repository(db_session, url="https://github.com/test/repo", name="test/repo", owner_id=user.id)

    # Create two analysis results for the repository
    analysis_create1 = schemas.AnalysisResultCreate(
        repository_id=repo.id,
        status=AnalysisStatus.PENDING,
        summary="Test Summary 1",
        narrative="Test Narrative 1",
        file_count=10,
        commit_count=5,
        total_lines=100,
        languages={"Python": 100},
        open_issues_count=1,
        open_pull_requests_count=2,
        contributors=[{"name": "test"}],
        tech_stack=["test"],
        report_url="http://test.com"
    )
    crud.create_analysis_result(db_session, analysis=analysis_create1)
    analysis_create2 = schemas.AnalysisResultCreate(
        repository_id=repo.id,
        status=AnalysisStatus.COMPLETED,
        summary="Test Summary 2",
        narrative="Test Narrative 2",
        file_count=20,
        commit_count=10,
        total_lines=200,
        languages={"Python": 200},
        open_issues_count=2,
        open_pull_requests_count=4,
        contributors=[{"name": "test2"}],
        tech_stack=["test2"],
        report_url="http://test2.com"
    )
    crud.create_analysis_result(db_session, analysis=analysis_create2)

    # Retrieve the analysis results for the repository
    analysis_results = crud.get_analysis_results_for_repository(db_session, repository_id=repo.id)
    assert len(analysis_results) == 2


def test_update_repository_status(db_session: Session):
    # Create a user and a repository
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    repo = crud.create_repository(db_session, url="https://github.com/test/repo", name="test/repo", owner_id=user.id)

    # Update the status
    updated_repo = crud.update_repository_status(db_session, repository_id=repo.id, new_status=AnalysisStatus.COMPLETED)
    assert updated_repo.status == AnalysisStatus.COMPLETED


def test_update_analysis_result_summary(db_session: Session):
    # Create a user, repository, and analysis result
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    repo = crud.create_repository(db_session, url="https://github.com/test/repo", name="test/repo", owner_id=user.id)
    analysis_create = schemas.AnalysisResultCreate(
        repository_id=repo.id,
        status=AnalysisStatus.PENDING,
        summary="Test Summary",
        narrative="Test Narrative",
        file_count=10,
        commit_count=5,
        total_lines=100,
        languages={"Python": 100},
        open_issues_count=1,
        open_pull_requests_count=2,
        contributors=[{"name": "test"}],
        tech_stack=["test"],
        report_url="http://test.com"
    )
    analysis = crud.create_analysis_result(db_session, analysis=analysis_create)

    # Update the summary
    updated_analysis = crud.update_analysis_result_summary(db_session, analysis_id=analysis.id, new_summary="New Summary")
    assert updated_analysis.summary == "New Summary"


def test_delete_repository(db_session: Session):
    # Create a user and a repository
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    repo = crud.create_repository(db_session, url="https://github.com/test/repo", name="test/repo", owner_id=user.id)

    # Delete the repository
    deleted_repo = crud.delete_repository(db_session, repository_id=repo.id)
    assert deleted_repo is not None
    assert crud.get_repository(db_session, repository_id=repo.id) is None


def test_delete_analysis_result(db_session: Session):
    # Create a user, repository, and analysis result
    user = models.User(username="testuser", hashed_password="testpassword")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    repo = crud.create_repository(db_session, url="https://github.com/test/repo", name="test/repo", owner_id=user.id)
    analysis_create = schemas.AnalysisResultCreate(
        repository_id=repo.id,
        status=AnalysisStatus.PENDING,
        summary="Test Summary",
        narrative="Test Narrative",
        file_count=10,
        commit_count=5,
        total_lines=100,
        languages={"Python": 100},
        open_issues_count=1,
        open_pull_requests_count=2,
        contributors=[{"name": "test"}],
        tech_stack=["test"],
        report_url="http://test.com"
    )
    analysis = crud.create_analysis_result(db_session, analysis=analysis_create)

    # Delete the analysis result
    deleted_analysis = crud.delete_analysis_result(db_session, analysis_id=analysis.id)
    assert deleted_analysis is not None
    assert crud.get_analysis_result(db_session, analysis_id=analysis.id) is None