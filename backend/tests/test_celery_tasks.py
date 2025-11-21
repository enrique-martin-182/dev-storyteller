from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.core.enums import AnalysisStatus
from src.db import models
from src.services.analysis_service import (
    clone_and_analyze_repository,
    generate_narratives_task,
)


@pytest.fixture(autouse=True)
def mock_celery_eager():
    """Ensure Celery tasks run eagerly for tests."""
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = False


@pytest.fixture
def mock_db_session():
    """Mock SessionLocal to return a MagicMock db_session."""
    mock_session = MagicMock(spec=Session)
    with patch("src.services.analysis_service.SessionLocal", return_value=mock_session):
        yield mock_session


@pytest.fixture
def mock_crud():
    """Mock the crud module."""
    with patch("src.services.analysis_service.crud", autospec=True) as mock:
        yield mock


@pytest.fixture
def mock_github_service():
    """Mock GitHubService."""
    with patch("src.services.analysis_service.GitHubService", autospec=True) as mock:
        yield mock.return_value


@pytest.fixture
def mock_repository_analyzer(_mock_github_service):
    """Mock RepositoryAnalyzer."""
    with patch(
        "src.services.analysis_service.RepositoryAnalyzer", autospec=True
    ) as mock:
        mock_instance = mock.return_value
        mock_instance.get_repository_analysis = AsyncMock(
            return_value={
                "file_count": 10,
                "commit_count": 50,
                "languages": {"Python": 1000},
                "open_issues_count": 5,
                "open_pull_requests_count": 2,
                "contributors": [{"name": "testuser"}],
                "tech_stack": ["Python", "FastAPI"],
                "file_structure": [],
                "commit_history": [],
            }
        )
        yield mock_instance


@pytest.fixture
def mock_narrative_generator():
    """Mock NarrativeGenerator."""
    with patch(
        "src.services.analysis_service.NarrativeGenerator", autospec=True
    ) as mock:
        mock_instance = mock.return_value
        mock_instance.generate_narrative.return_value = "Comprehensive narrative"
        mock_instance.generate_recruiter_summary = MagicMock(
            return_value="Recruiter summary"
        )
        yield mock_instance


@pytest.fixture
def mock_broadcast_status_update():
    """Mock _broadcast_status_update."""
    with patch(
        "src.services.analysis_service._broadcast_status_update", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.fixture
def sample_repository():
    """Returns a sample Repository model instance."""
    return models.Repository(
        id=1,
        url="https://github.com/test/repo",
        name="test_repo",
        owner_id=1,
        status=AnalysisStatus.PENDING,
    )


@pytest.fixture
def sample_analysis_result():
    """Returns a sample AnalysisResult model instance."""
    return models.AnalysisResult(
        id=1,
        repository_id=1,
        status=AnalysisStatus.PENDING,
        summary="Initial summary",
        narrative="Initial narrative",
    )


class TestCeleryTasks:
    def test_clone_and_analyze_repository_success(
        self,
        mock_db_session,
        mock_crud,
        mock_repository_analyzer,
        mock_broadcast_status_update,
        sample_repository,
    ):
        mock_crud.get_repository.return_value = sample_repository
        analysis_result = models.AnalysisResult(repository_id=sample_repository.id)
        mock_crud.create_analysis_result.return_value = analysis_result

        with patch("src.services.analysis_service.generate_narratives_task.delay") as mock_delay:
            clone_and_analyze_repository(sample_repository.id, db=mock_db_session)

        mock_crud.get_repository.assert_called_with(mock_db_session, sample_repository.id)
        mock_repository_analyzer.get_repository_analysis.assert_called_once_with(sample_repository.url)
        mock_broadcast_status_update.assert_any_call(sample_repository.id, AnalysisStatus.IN_PROGRESS)
        mock_broadcast_status_update.assert_any_call(sample_repository.id, AnalysisStatus.COMPLETED)
        assert sample_repository.status == AnalysisStatus.COMPLETED
        mock_crud.create_analysis_result.assert_called_once()
        mock_delay.assert_called_once()

    def test_clone_and_analyze_repository_failure(
        self,
        mock_db_session,
        mock_crud,
        mock_repository_analyzer,
        mock_broadcast_status_update,
        sample_repository,
    ):
        # Arrange
        mock_crud.get_repository.return_value = sample_repository

        # Configure the mock analyzer to raise an exception when get_repository_analysis is called
        mock_repository_analyzer.get_repository_analysis.side_effect = Exception("GitHub API error")

        # Mock the query to return no existing analysis result
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act
        # The exception is caught inside, so we don't need a with pytest.raises
        clone_and_analyze_repository(sample_repository.id, db=mock_db_session)

        # Assert
        # Verify repository status is updated to FAILED
        mock_crud.get_repository.assert_called_with(mock_db_session, sample_repository.id)
        assert sample_repository.status == AnalysisStatus.FAILED

        # Verify status updates were broadcast
        mock_broadcast_status_update.assert_any_call(sample_repository.id, AnalysisStatus.IN_PROGRESS)
        mock_broadcast_status_update.assert_any_call(sample_repository.id, AnalysisStatus.FAILED)

        # Verify that an error summary was set on the analysis result
        added_object = None
        for call in mock_db_session.add.call_args_list:
            args, _ = call
            if isinstance(args[0], models.AnalysisResult):
                added_object = args[0]
                break

        assert added_object is not None, "AnalysisResult was not created and added to the session"
        assert "An unexpected error occurred during analysis: GitHub API error" in added_object.summary

        # Verify the analyzer was called
        mock_repository_analyzer.get_repository_analysis.assert_called_once_with(sample_repository.url)

    def test_clone_and_analyze_repository_not_found(
        self, mock_db_session, mock_crud, mock_broadcast_status_update
    ):
        mock_crud.get_repository.return_value = None
        clone_and_analyze_repository(999, db=mock_db_session)
        mock_crud.get_repository.assert_called_once_with(mock_db_session, 999)
        mock_broadcast_status_update.assert_not_called()

    def test_generate_narratives_task_success(
        self,
        mock_db_session,
        mock_narrative_generator,
        sample_analysis_result,
    ):
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_analysis_result
        repo_analysis_data = {"file_structure": [], "commit_history": []}

        # Configurar mock_db_session.refresh para que copie los cambios a sample_analysis_result
        def mock_refresh_side_effect(instance):
            if instance.id == sample_analysis_result.id:
                sample_analysis_result.summary = instance.summary
                sample_analysis_result.narrative = instance.narrative
        mock_db_session.refresh.side_effect = mock_refresh_side_effect

        with patch("src.services.analysis_service.asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = mock_narrative_generator.generate_recruiter_summary.return_value
            generate_narratives_task(1, repo_analysis_data, db=mock_db_session)

        mock_narrative_generator.generate_narrative.assert_called_once_with(repo_analysis_data)
        mock_narrative_generator.generate_recruiter_summary.assert_called_once_with(repo_analysis_data)
        assert sample_analysis_result.summary == "Recruiter summary"
        assert sample_analysis_result.narrative == "Comprehensive narrative"
        mock_db_session.add.assert_called_once_with(sample_analysis_result)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_analysis_result)

    def test_generate_narratives_task_failure(
        self,
        mock_db_session,
        mock_narrative_generator,
        sample_analysis_result,
    ):
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_analysis_result
        mock_narrative_generator.generate_narrative.side_effect = Exception("LLM error")
        repo_analysis_data = {"file_structure": [], "commit_history": []}

        with patch("src.services.analysis_service.logging.error") as mock_logging_error, \
             patch("src.services.analysis_service.asyncio.run") as mock_asyncio_run:
                # Mock the behavior of asyncio.run if it's called
                mock_asyncio_run.return_value = None
                generate_narratives_task(1, repo_analysis_data, db=mock_db_session)
                mock_logging_error.assert_called_once()

    def test_generate_narratives_task_analysis_result_not_found(
        self,
        mock_db_session,
        mock_narrative_generator,
    ):
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        repo_analysis_data = {"file_structure": [], "commit_history": []}

        with patch("src.services.analysis_service.logging.warning") as mock_logging_warning, \
             patch("src.services.analysis_service.asyncio.run") as mock_asyncio_run:
                # Mock the behavior of asyncio.run if it's called
                mock_asyncio_run.return_value = None
                generate_narratives_task(999, repo_analysis_data, db=mock_db_session)
                mock_logging_warning.assert_called_once()
        mock_narrative_generator.generate_narrative.assert_not_called()
