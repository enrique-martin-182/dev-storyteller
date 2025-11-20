import os
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import pytest
from sqlalchemy.orm import Session

from src.core.enums import AnalysisStatus
from src.db import models
from src.services.analysis_service import clone_and_analyze_repository


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
    return repo


@pytest.mark.asyncio
async def test_clone_and_analyze_repository_success_isolated(
    mock_db_session, mock_repository
):
    with patch(
        "src.services.analysis_service.crud", autospec=True
    ) as mock_crud, patch(
        "src.services.analysis_service.RepositoryAnalyzer", autospec=True
    ) as mock_repository_analyzer, patch(
        "src.services.analysis_service.generate_narratives_task", autospec=True
    ) as mock_generate_narratives_task, patch(
        "os.getenv", side_effect=lambda key: "mock_token" if key == "GITHUB_TOKEN" else os.getenv(key)
    ):

        # Arrange
        mock_crud.get_repository.return_value = mock_repository
        mock_repository_analyzer_instance = (
            mock_repository_analyzer.return_value
        )
        analysis_data = {
            "file_count": 10,
            "commit_count": 20,
            "languages": {"Python": 100},
            "open_issues_count": 5,
            "open_pull_requests_count": 2,
            "contributors": [{"name": "contributor1"}], # Added contributors
            "tech_stack": ["Python"],
            "file_structure": [],
            "commit_history": [],
        }
        mock_repository_analyzer_instance.get_repository_analysis.return_value = AsyncMock(return_value=analysis_data)
        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.side_effect = [
                None, # for _broadcast_status_update
                analysis_data,
                None # for _broadcast_status_update
            ]

            # Act
            clone_and_analyze_repository(mock_repository.id, db=mock_db_session)
        # Assert
        mock_crud.get_repository.assert_called_once_with(
            mock_db_session, mock_repository.id
        )
        assert mock_repository.status == AnalysisStatus.COMPLETED
        mock_generate_narratives_task.delay.assert_called_once()
