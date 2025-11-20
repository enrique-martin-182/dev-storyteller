from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.api.v1 import schemas
from src.db import models
from src.services import repository_service


# Fixture for a mock database session
@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

# Fixture for a mock repository object
@pytest.fixture
def mock_repository():
    repo = MagicMock(spec=models.Repository)
    repo.id = 1
    repo.url = "https://github.com/owner/repo_name"
    repo.name = "owner/repo_name"
    repo.owner_username = "test_user"
    repo.owner_id = 1
    return repo

# Test cases for extract_repo_name_from_url
def test_extract_repo_name_from_url_success():
    url = "https://github.com/owner/repo_name"
    expected = "owner/repo_name"
    assert repository_service.extract_repo_name_from_url(url) == expected

def test_extract_repo_name_from_url_with_git_extension():
    url = "https://github.com/owner/repo_name.git"
    expected = "owner/repo_name"
    assert repository_service.extract_repo_name_from_url(url) == expected

def test_extract_repo_name_from_url_invalid_format():
    url = "https://invalid-url.com/owner/repo_name"
    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        repository_service.extract_repo_name_from_url(url)

def test_extract_repo_name_from_url_empty_string():
    url = ""
    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        repository_service.extract_repo_name_from_url(url)

# Test cases for get_repository_by_url
def test_get_repository_by_url_exists(mock_db_session, mock_repository):
    mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_repository
    repo = repository_service.get_repository_by_url(mock_db_session, mock_repository.url)
    assert repo == mock_repository
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_db_session.query.return_value.options.return_value.filter.assert_called_once()

def test_get_repository_by_url_not_exists(mock_db_session):
    mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
    repo = repository_service.get_repository_by_url(mock_db_session, "https://github.com/nonexistent/repo")
    assert repo is None
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_db_session.query.return_value.options.return_value.filter.assert_called_once()

# Test cases for create_repository
@patch("src.services.repository_service.extract_repo_name_from_url")
@patch("src.services.repository_service.crud.create_repository")
@patch("src.services.repository_service.analysis_service.clone_and_analyze_repository.delay")
def test_create_repository_success(
    mock_delay, mock_crud_create_repository, mock_extract_repo_name_from_url, mock_db_session, mock_repository
):
    mock_extract_repo_name_from_url.return_value = mock_repository.name
    mock_crud_create_repository.return_value = mock_repository
    repo_create_schema = schemas.RepositoryCreate(url=mock_repository.url)

    db_repo = repository_service.create_repository(mock_db_session, repo_create_schema, mock_repository.owner_id)

    mock_extract_repo_name_from_url.assert_called_once_with(str(repo_create_schema.url))
    mock_crud_create_repository.assert_called_once_with(
        db=mock_db_session,
        url=str(repo_create_schema.url),
        name=mock_repository.name,
        owner_id=mock_repository.owner_id,
    )
    mock_delay.assert_called_once_with(mock_repository.id)
    assert db_repo == mock_repository

@patch("src.services.repository_service.extract_repo_name_from_url")
@patch("src.services.repository_service.crud.create_repository")
@patch("src.services.repository_service.analysis_service.clone_and_analyze_repository.delay")
def test_create_repository_invalid_url(
    mock_delay, mock_crud_create_repository, mock_extract_repo_name_from_url, mock_db_session
):
    mock_extract_repo_name_from_url.side_effect = ValueError("Invalid GitHub URL format")
    repo_create_schema = schemas.RepositoryCreate(url="https://github.com/invalid/url")

    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        repository_service.create_repository(mock_db_session, repo_create_schema, "test_user")

    mock_extract_repo_name_from_url.assert_called_once_with(str(repo_create_schema.url))
    mock_crud_create_repository.assert_not_called()
    mock_delay.assert_not_called()

# Test cases for get_repositories
def test_get_repositories_by_owner_multiple(mock_db_session, mock_repository):
    mock_query = MagicMock()
    mock_filter_result = MagicMock()
    mock_options_result = MagicMock()
    mock_offset_result = MagicMock()
    mock_limit_result = MagicMock()

    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter_result
    mock_filter_result.options.return_value = mock_options_result
    mock_options_result.offset.return_value = mock_offset_result
    mock_offset_result.limit.return_value = mock_limit_result
    mock_limit_result.all.return_value = [mock_repository, mock_repository]
    
    repos = repository_service.get_repositories_by_owner(mock_db_session, owner_id=mock_repository.owner_id)
    assert len(repos) == 2
    assert repos[0] == mock_repository
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_query.filter.assert_called_once()
    mock_filter_result.options.assert_called_once()
    mock_options_result.offset.assert_called_once_with(0)
    mock_offset_result.limit.assert_called_once_with(100)

def test_get_repositories_by_owner_empty(mock_db_session):
    mock_query = MagicMock()
    mock_filter_result = MagicMock()
    mock_options_result = MagicMock()
    mock_offset_result = MagicMock()
    mock_limit_result = MagicMock()

    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter_result
    mock_filter_result.options.return_value = mock_options_result
    mock_options_result.offset.return_value = mock_offset_result
    mock_offset_result.limit.return_value = mock_limit_result
    mock_limit_result.all.return_value = []

    repos = repository_service.get_repositories_by_owner(mock_db_session, owner_id=1)
    assert len(repos) == 0
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_query.filter.assert_called_once()
    mock_filter_result.options.assert_called_once()
    mock_options_result.offset.assert_called_once_with(0)
    mock_offset_result.limit.assert_called_once_with(100)

def test_get_repositories_by_owner_with_skip_limit(mock_db_session, mock_repository):
    mock_query = MagicMock()
    mock_filter_result = MagicMock()
    mock_options_result = MagicMock()
    mock_offset_result = MagicMock()
    mock_limit_result = MagicMock()

    mock_db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter_result
    mock_filter_result.options.return_value = mock_options_result
    mock_options_result.offset.return_value = mock_offset_result
    mock_offset_result.limit.return_value = mock_limit_result
    mock_limit_result.all.return_value = [mock_repository]

    repos = repository_service.get_repositories_by_owner(mock_db_session, owner_id=1, skip=1, limit=10)
    assert len(repos) == 1
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_query.filter.assert_called_once()
    mock_filter_result.options.assert_called_once()
    mock_options_result.offset.assert_called_once_with(1)
    mock_offset_result.limit.assert_called_once_with(10)

# Test cases for get_repository
def test_get_repository_exists(mock_db_session, mock_repository):
    mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = mock_repository
    repo = repository_service.get_repository(mock_db_session, 1)
    assert repo == mock_repository
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_db_session.query.return_value.options.return_value.filter.assert_called_once()

def test_get_repository_not_exists(mock_db_session):
    mock_db_session.query.return_value.options.return_value.filter.return_value.first.return_value = None
    repo = repository_service.get_repository(mock_db_session, 999)
    assert repo is None
    mock_db_session.query.assert_called_once_with(models.Repository)
    mock_db_session.query.return_value.options.return_value.filter.assert_called_once()

# Test cases for get_analysis_results_for_repository
@pytest.fixture
def mock_analysis_result():
    analysis = MagicMock(spec=models.AnalysisResult)
    analysis.id = 1
    analysis.repository_id = 1
    analysis.narrative = "Test narrative"
    return analysis

def test_get_analysis_results_for_repository_exists(mock_db_session, mock_analysis_result):
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_analysis_result]
    results = repository_service.get_analysis_results_for_repository(mock_db_session, 1)
    assert len(results) == 1
    assert results[0] == mock_analysis_result
    mock_db_session.query.assert_called_once_with(models.AnalysisResult)
    mock_db_session.query.return_value.filter.assert_called_once()

def test_get_analysis_results_for_repository_not_exists(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.all.return_value = []
    results = repository_service.get_analysis_results_for_repository(mock_db_session, 999)
    assert len(results) == 0
    mock_db_session.query.assert_called_once_with(models.AnalysisResult)
    mock_db_session.query.return_value.filter.assert_called_once()

# Test cases for get_analysis_narrative
def test_get_analysis_narrative_exists(mock_db_session, mock_analysis_result):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_analysis_result
    narrative = repository_service.get_analysis_narrative(mock_db_session, 1)
    assert narrative == mock_analysis_result.narrative
    mock_db_session.query.assert_called_once_with(models.AnalysisResult)
    mock_db_session.query.return_value.filter.assert_called_once()

def test_get_analysis_narrative_no_narrative(mock_db_session, mock_analysis_result):
    mock_analysis_result.narrative = None
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_analysis_result
    narrative = repository_service.get_analysis_narrative(mock_db_session, 1)
    assert narrative is None
    mock_db_session.query.assert_called_once_with(models.AnalysisResult)
    mock_db_session.query.return_value.filter.assert_called_once()

def test_get_analysis_narrative_analysis_not_exists(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    narrative = repository_service.get_analysis_narrative(mock_db_session, 999)
    assert narrative is None
    mock_db_session.query.assert_called_once_with(models.AnalysisResult)
    mock_db_session.query.return_value.filter.assert_called_once()
