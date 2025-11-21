
import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.api.v1 import schemas
from src.services.repository_service import RepositoryService


class TestRepositoryService(unittest.TestCase):

    def setUp(self):
        # We need to access the mocker fixture, but setUp is not a fixture.
        # So we will create our own mocks here using patch.
        self.mock_crud = MagicMock()
        self.mock_analysis_service = MagicMock()

        self.repository_service = RepositoryService(crud_module=self.mock_crud, analysis_service_module=self.mock_analysis_service)

    def tearDown(self):
        pass


    def test_extract_repo_name_from_url(self):
        # Test with a valid URL
        url = "https://github.com/owner/repo_name"
        repo_name = self.repository_service.extract_repo_name_from_url(url)
        self.assertEqual(repo_name, "owner/repo_name")

        # Test with a .git extension
        url = "https://github.com/owner/repo_name.git"
        repo_name = self.repository_service.extract_repo_name_from_url(url)
        self.assertEqual(repo_name, "owner/repo_name")

        # Test with an invalid URL
        with self.assertRaises(ValueError):
            self.repository_service.extract_repo_name_from_url("invalid_url")

    def test_get_repository_by_url(self):
        # Mock the database session
        mock_db = MagicMock(spec=Session)
        # Call the service function
        self.repository_service.get_repository_by_url(mock_db, "some_url")
        # Assert that the CRUD function was called
        self.mock_crud.get_repository_by_url.assert_called_once_with(mock_db, "some_url")

    def test_create_repository(self):
        # Mock the database session
        mock_db = MagicMock(spec=Session)
        repo_create = schemas.RepositoryCreate(url="https://github.com/owner/repo_name")
        # Call the service function
        self.repository_service.create_repository(mock_db, repo_create, 1)
        # Assert that the CRUD function was called
        self.mock_crud.create_repository.assert_called_once_with(db=mock_db, url="https://github.com/owner/repo_name", name="owner/repo_name", owner_id=1)
        # Assert that the analysis service was called
        self.mock_analysis_service.clone_and_analyze_repository.delay.assert_called_once()

    def test_get_repositories_by_owner(self):
        # Mock the database session
        mock_db = MagicMock(spec=Session)
        # Call the service function
        self.repository_service.get_repositories_by_owner(mock_db, 1)
        # Assert that the CRUD function was called
        self.mock_crud.get_repositories_by_owner.assert_called_once_with(mock_db, owner_id=1, skip=0, limit=100)

    def test_get_repository(self):
        # Mock the database session
        mock_db = MagicMock(spec=Session)
        # Call the service function
        self.repository_service.get_repository(mock_db, 1)
        # Assert that the CRUD function was called
        self.mock_crud.get_repository.assert_called_once_with(mock_db, 1)

    def test_get_analysis_results_for_repository(self):
        # Mock the database session
        mock_db = MagicMock(spec=Session)
        # Call the service function
        self.repository_service.get_analysis_results_for_repository(mock_db, 1)
        # Assert that the CRUD function was called
        self.mock_crud.get_analysis_results_for_repository.assert_called_once_with(mock_db, 1)

    def test_get_analysis_narrative(self):
        # Mock the database session
        mock_db = MagicMock(spec=Session)
        # Mock the return value of the CRUD function
        mock_analysis_result = MagicMock()
        mock_analysis_result.narrative = "test_narrative"
        self.mock_crud.get_analysis_result.return_value = mock_analysis_result
        # Call the service function
        narrative = self.repository_service.get_analysis_narrative(mock_db, 1)
        # Assert that the CRUD function was called
        self.mock_crud.get_analysis_result.assert_called_once_with(mock_db, 1)
        # Assert that the correct narrative is returned
        self.assertEqual(narrative, "test_narrative")

        # Test case where analysis result is not found
        self.mock_crud.get_analysis_result.return_value = None
        narrative = self.repository_service.get_analysis_narrative(mock_db, 1)
        self.assertIsNone(narrative)
