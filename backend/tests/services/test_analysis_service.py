
import unittest
from unittest.mock import MagicMock, patch, ANY

from sqlalchemy.orm import Session

from src.core.enums import AnalysisStatus
from src.services import analysis_service
from src.db import models
from src.api.v1 import schemas


class TestAnalysisService(unittest.TestCase):

    @patch("src.services.analysis_service.SessionLocal")
    @patch("src.services.analysis_service.crud")
    @patch("src.services.analysis_service.asyncio.run")
    @patch("src.services.analysis_service.GitHubService")
    @patch("src.services.analysis_service.RepositoryAnalyzer")
    @patch("src.services.analysis_service.generate_narratives_task")
    def test_clone_and_analyze_repository_success(
        self,
        mock_generate_narratives_task,
        mock_repository_analyzer,
        mock_github_service,
        mock_asyncio_run,
        mock_crud,
        mock_session_local,
    ):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_repo = MagicMock(spec=models.Repository)
        mock_repo.id = 1
        mock_repo.url = "https://github.com/owner/repo"
        mock_crud.get_repository.return_value = mock_repo
        mock_analyzer_instance = mock_repository_analyzer.return_value
        mock_asyncio_run.return_value = {
            "file_count": 10,
            "commit_count": 50,
            "languages": {"Python": 100},
            "open_issues_count": 5,
            "open_pull_requests_count": 2,
            "contributors": [{"login": "testuser", "contributions": 10}],
            "tech_stack": ["Python"],
        }

        # Act
        analysis_service.clone_and_analyze_repository(1)

        # Assert
        mock_crud.get_repository.assert_called_once_with(mock_db, 1)
        self.assertEqual(mock_repo.status, AnalysisStatus.COMPLETED)
        mock_db.commit.call_count == 2
        mock_asyncio_run.call_count == 2
        mock_github_service.assert_called_once()
        mock_repository_analyzer.assert_called_once_with(mock_github_service.return_value)
        mock_generate_narratives_task.delay.assert_called_once_with(1, ANY)
        mock_crud.create_analysis_result.assert_called_once()

    @patch("src.services.analysis_service.SessionLocal")
    @patch("src.services.analysis_service.crud")
    def test_clone_and_analyze_repository_repo_not_found(
        self, mock_crud, mock_session_local
    ):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_crud.get_repository.return_value = None

        # Act
        analysis_service.clone_and_analyze_repository(1)

        # Assert
        mock_crud.get_repository.assert_called_once_with(mock_db, 1)
        mock_db.commit.assert_not_called()

    @patch("src.services.analysis_service.SessionLocal")
    @patch("src.services.analysis_service.crud")
    def test_clone_and_analyze_repository_exception(
        self, mock_crud, mock_session_local
    ):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_crud.get_repository.side_effect = Exception("Test Exception")

        # Act & Assert
        with self.assertRaises(Exception):
            analysis_service.clone_and_analyze_repository(1)


    @patch("src.services.analysis_service.SessionLocal")
    @patch("src.services.analysis_service.NarrativeGenerator")
    @patch("src.services.analysis_service.asyncio.run")
    def test_generate_narratives_task_success(
        self, mock_asyncio_run, mock_narrative_generator, mock_session_local
    ):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_analysis_result = MagicMock(spec=models.AnalysisResult)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis_result
        mock_narrative_generator_instance = mock_narrative_generator.return_value
        mock_narrative_generator_instance.generate_narrative.return_value = "Comprehensive Narrative"
        mock_asyncio_run.return_value = "Recruiter Summary"

        repo_analysis = {"some": "data"}

        # Act
        analysis_service.generate_narratives_task(1, repo_analysis)

        # Assert
        mock_db.query.assert_called_once_with(models.AnalysisResult)
        mock_narrative_generator.assert_called_once()
        mock_narrative_generator_instance.generate_narrative.assert_called_once_with(repo_analysis)
        mock_asyncio_run.assert_called_once_with(mock_narrative_generator_instance.generate_recruiter_summary(repo_analysis))
        self.assertEqual(mock_analysis_result.summary, "Recruiter Summary")
        self.assertEqual(mock_analysis_result.narrative, "Comprehensive Narrative")
        mock_db.add.assert_called_once_with(mock_analysis_result)
        mock_db.commit.assert_called_once()

    @patch("src.services.analysis_service.SessionLocal")
    @patch("src.services.analysis_service.NarrativeGenerator")
    def test_generate_narratives_task_analysis_not_found(
        self, mock_narrative_generator, mock_session_local
    ):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        repo_analysis = {"some": "data"}

        # Act
        analysis_service.generate_narratives_task(1, repo_analysis)

        # Assert
        mock_db.query.assert_called_once_with(models.AnalysisResult)
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("src.services.analysis_service.SessionLocal")
    @patch("src.services.analysis_service.NarrativeGenerator")
    def test_generate_narratives_task_exception(
        self, mock_narrative_generator, mock_session_local
    ):
        # Arrange
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        mock_db.query.side_effect = Exception("Test Exception")
        repo_analysis = {"some": "data"}

        # Act
        analysis_service.generate_narratives_task(1, repo_analysis)

        # Assert
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
