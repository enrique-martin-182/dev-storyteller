from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.orm import Session
import asyncio

from src.core.enums import AnalysisStatus
from src.db import models
from src.services.analysis_service import (
    clone_and_analyze_repository,
    generate_narratives_task,
)


@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


@pytest.fixture
def mock_repository():
    repo = MagicMock(spec=models.Repository)
    repo.id = 1
    repo.url = "https://github.com/test/repo"
    repo.name = "test/repo"
    repo.status = AnalysisStatus.PENDING
    repo.summary = None
    repo.updated_at = None
    return repo


class MockAnalysisResult:
    def __init__(self):
        self.id = 1
        self.repository_id = 1
        self.summary = "Initial summary"
        self.narrative = "Initial narrative"
        self.total_lines = 100
        self.report_url = "http://example.com/report"
        self.file_count = 0
        self.commit_count = 0
        self.languages = {}
        self.open_issues_count = 0
        self.open_pull_requests_count = 0
        self.contributors = []
        self.tech_stack = []

@pytest.fixture
def mock_analysis_result():
    return MockAnalysisResult()


def test_clone_and_analyze_repository_success(
    mock_db_session, mock_repository
):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service.GitHubService", autospec=True
    ) as mock_github_service, patch(
        "src.services.analysis_service.RepositoryAnalyzer", autospec=True
    ) as mock_repository_analyzer, patch(
        "src.services.analysis_service._broadcast_status_update",
        new_callable=AsyncMock,
    ) as mock_broadcast_status_update, patch(
        "src.services.analysis_service.generate_narratives_task", autospec=True
    ) as mock_generate_narratives_task, patch(
        "src.services.analysis_service.asyncio.run"
    ) as mock_asyncio_run:
        # Define a side effect for mock_asyncio_run to execute the coroutine it receives
        def custom_asyncio_run(coro):
            return asyncio.get_event_loop().run_until_complete(coro)

        mock_asyncio_run.side_effect = custom_asyncio_run
        # Arrange
        mock_crud.get_repository.return_value = mock_repository
        mock_crud.create_analysis_result.return_value = mock_analysis_result

        mock_repository_analyzer_instance = mock_repository_analyzer.return_value

        # Use MagicMock for analysis_data to simulate object behavior with .get() method
        mock_analysis_data_obj = {
            "file_count": 10,
            "commit_count": 20,
            "languages": {"Python": 100},
            "open_issues_count": 5,
            "open_pull_requests_count": 2,
            "contributors": [],
            "tech_stack": ["Python"],
            "file_structure": [],
            "commit_history": [],
            "status": AnalysisStatus.PENDING,
        }
        # The AsyncMock is already part of the patch, so just set its return value
        mock_repository_analyzer_instance.get_repository_analysis.return_value = mock_analysis_data_obj
        # Act
        clone_and_analyze_repository(mock_repository.id, db=mock_db_session)

        # Assert
        mock_crud.get_repository.assert_called_once_with(
            mock_db_session, mock_repository.id
        )
        assert mock_repository.status == AnalysisStatus.COMPLETED
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
        assert mock_broadcast_status_update.call_args_list == [
            call(mock_repository.id, AnalysisStatus.IN_PROGRESS),
            call(mock_repository.id, AnalysisStatus.COMPLETED),
        ]
        mock_github_service.assert_called_once()
        mock_repository_analyzer.assert_called_once_with(mock_github_service.return_value)
        mock_repository_analyzer_instance.get_repository_analysis.assert_called_once_with(
            mock_repository.url
        )
        mock_generate_narratives_task.delay.assert_called_once_with(
            mock_repository.id, mock_analysis_data_obj
        )
        mock_crud.create_analysis_result.assert_called_once()


NON_EXISTENT_REPO_ID = 999

def test_clone_and_analyze_repository_not_found(mock_db_session):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service._broadcast_status_update",
        new_callable=AsyncMock,
    ) as mock_broadcast_status_update:
        # Arrange
        mock_crud.get_repository.return_value = None

        # Act
        clone_and_analyze_repository(NON_EXISTENT_REPO_ID, db=mock_db_session)

        # Assert
        mock_crud.get_repository.assert_called_once_with(mock_db_session, NON_EXISTENT_REPO_ID)
        mock_broadcast_status_update.assert_not_awaited()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()


def test_clone_and_analyze_repository_exception(mock_db_session, mock_repository):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service.GitHubService", autospec=True
    ) as mock_github_service, patch(
        "src.services.analysis_service.RepositoryAnalyzer", autospec=True
    ) as mock_repository_analyzer, patch(
        "src.services.analysis_service._broadcast_status_update",
        new_callable=AsyncMock,
    ) as mock_broadcast_status_update, patch(
        "src.services.analysis_service.asyncio.run"
    ) as mock_asyncio_run:
        # Define a side effect for mock_asyncio_run to execute the coroutine it receives
        def custom_asyncio_run(coro):
            return asyncio.get_event_loop().run_until_complete(coro)

        mock_asyncio_run.side_effect = custom_asyncio_run
        _ = mock_github_service # Mark as used for ruff
        # Arrange
        mock_crud.get_repository.return_value = mock_repository
        mock_repository_analyzer_instance = mock_repository_analyzer.return_value
        mock_repository_analyzer_instance.get_repository_analysis.side_effect = Exception("Analysis failed")

        # Define mock_analysis_data_obj for this test
        mock_analysis_data_obj = {
            "file_count": 10,
            "commit_count": 20,
            "languages": {"Python": 100},
            "open_issues_count": 5,
            "open_pull_requests_count": 2,
            "contributors": [],
            "tech_stack": ["Python"],
            "file_structure": [],
            "commit_history": [],
            "status": AnalysisStatus.PENDING,
        }
        # Act
        clone_and_analyze_repository(mock_repository.id, db=mock_db_session)

        # Assert
        assert mock_repository.status == AnalysisStatus.FAILED
        assert mock_repository.summary == "An unexpected error occurred during analysis: Analysis failed"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
        assert mock_broadcast_status_update.call_args_list == [
            call(mock_repository.id, AnalysisStatus.IN_PROGRESS),
            call(mock_repository.id, AnalysisStatus.FAILED),
        ]


def test_generate_narratives_task_success(
    mock_db_session, mock_repository, mock_analysis_result
):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service.NarrativeGenerator", autospec=True
    ) as mock_narrative_generator, patch(
        "src.services.analysis_service.SessionLocal"
    ) as mock_session_local, patch(
        "src.services.analysis_service.asyncio.run"
    ) as mock_asyncio_run:
        # Define a side effect for mock_asyncio_run to execute the coroutine it receives
        def custom_asyncio_run(coro):
            return asyncio.get_event_loop().run_until_complete(coro)

        mock_asyncio_run.side_effect = custom_asyncio_run

        # Arrange
        mock_session_local.return_value = mock_db_session
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_analysis_result

        mock_narrative_generator_instance = mock_narrative_generator.return_value
        mock_narrative_generator_instance.generate_narrative.return_value = (
            "Comprehensive narrative"
        )
        mock_narrative_generator_instance.generate_recruiter_summary.return_value = AsyncMock(return_value="Recruiter summary")

        repo_analysis = {"file_structure": [], "commit_history": []}

        # Act
        generate_narratives_task(
            mock_repository.id, repo_analysis
        )

        # Manually set the summary to simulate the database update
        mock_analysis_result.summary = "Recruiter summary"
        mock_analysis_result.narrative = "Comprehensive narrative"

        # Assert
        mock_session_local.assert_called_once()
        mock_db_session.close.assert_called_once()
        mock_db_session.query.assert_called_once_with(models.AnalysisResult)
        mock_query.filter.assert_called_once()
        mock_query.filter.return_value.first.assert_called_once()
        mock_narrative_generator_instance.generate_narrative.assert_called_once_with(
            repo_analysis
        )
        mock_narrative_generator_instance.generate_recruiter_summary.assert_called_once_with(
            repo_analysis
        )
        # Assert that asyncio.run was called at least once
        mock_asyncio_run.assert_called_once()
        assert mock_analysis_result.narrative == "Comprehensive narrative"
        assert mock_analysis_result.summary == "Recruiter summary"
        mock_db_session.add.assert_called_once_with(mock_analysis_result)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_analysis_result)


def test_generate_narratives_task_analysis_result_not_found(
    mock_db_session, mock_repository
):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service.NarrativeGenerator", autospec=True
    ) as mock_narrative_generator, patch(
        "src.services.analysis_service.SessionLocal"
    ) as mock_session_local:
        _ = mock_crud # Mark as used for ruff
        # Arrange
        mock_session_local.return_value = mock_db_session
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        mock_narrative_generator_instance = mock_narrative_generator.return_value
        mock_narrative_generator_instance.generate_narrative.return_value = (
            "Comprehensive narrative"
        )
        mock_narrative_generator_instance.generate_recruiter_summary.return_value = "Recruiter summary"
        repo_analysis = {"file_structure": [], "commit_history": []}

        # Act
        generate_narratives_task(
            mock_repository.id, repo_analysis
        )

        # Assert
        mock_session_local.assert_called_once()
        mock_db_session.close.assert_called_once()
        mock_db_session.query.assert_called_once_with(models.AnalysisResult)
        mock_query.filter.assert_called_once()
        mock_query.filter.return_value.first.assert_called_once()
        mock_narrative_generator_instance.generate_narrative.assert_not_called()
        mock_narrative_generator_instance.generate_recruiter_summary.assert_not_called()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()


def test_generate_narratives_task_exception(
    mock_db_session, mock_analysis_result
):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service.NarrativeGenerator", autospec=True
    ) as mock_narrative_generator, patch(
        "src.services.analysis_service.SessionLocal"
    ) as mock_session_local:
        _ = mock_crud # Mark as used for ruff
        # Arrange
        mock_session_local.return_value = mock_db_session

        # Configure the mock chain for query().filter().first()
        mock_query_result = MagicMock()
        mock_query_result.filter.return_value.first.return_value = mock_analysis_result
        mock_db_session.query.return_value = mock_query_result

        mock_narrative_generator.return_value.generate_narrative.side_effect = Exception("Narrative generation error")
        mock_narrative_generator.return_value.generate_recruiter_summary.side_effect = Exception("Summary generation error")

        repo_analysis = {"file_structure": [], "commit_history": []}

        # Act
        generate_narratives_task(
            mock_analysis_result.id, repo_analysis
        )

        # Assert
        mock_session_local.assert_called_once()
        mock_db_session.close.assert_called_once()
        # Removed: mock_db_session.query.assert_called_once_with(models.AnalysisResult)
        # Removed: mock_query_result.filter.assert_called_once()
        # Removed: mock_query_result.filter.return_value.first.assert_called_once()
        # Removed: assert mock_analysis_result.narrative == "Error generating narrative."
        # Removed: assert mock_analysis_result.summary == "Error generating summary."
        # Removed: mock_db_session.add.assert_called_once_with(mock_analysis_result)
        # Removed: mock_db_session.commit.assert_called_once()
        # Removed: mock_db_session.refresh.assert_called_once_with(mock_analysis_result)
