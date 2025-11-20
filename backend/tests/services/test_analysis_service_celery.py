from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.enums import AnalysisStatus
from src.db import models
from src.db.database import Base
from src.services import analysis_service

# Configuración de la base de datos en memoria para las pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Fixture para crear una nueva sesión de base de datos y un esquema limpio
    para cada prueba.
    """
    Base.metadata.create_all(bind=engine)  # Crea las tablas
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)  # Elimina las tablas

@pytest.fixture(autouse=True)
def celery_eager_app(monkeypatch):
    monkeypatch.setattr("src.celery_app.celery_app.conf.CELERY_ALWAYS_EAGER", True)
    monkeypatch.setattr("src.celery_app.celery_app.conf.CELERY_RESULT_BACKEND", "cache")

@pytest.fixture
def mock_repository_analyzer():
    with patch("src.services.analysis_service.RepositoryAnalyzer") as mock:
        yield mock.return_value

@pytest.fixture
def mock_narrative_generator():
    with patch("src.services.analysis_service.NarrativeGenerator") as mock:
        yield mock.return_value

@pytest.fixture
def mock_connection_manager():
    with patch("src.api.v1.connection_manager.manager") as mock:
        mock.broadcast = AsyncMock()
        yield mock

def test_clone_and_analyze_repository_success(db_session, mock_repository_analyzer, mock_narrative_generator, mock_connection_manager, mocker):
    # Mockear _broadcast_status_update para evitar llamadas reales y warnings
    mocker.patch("src.services.analysis_service._broadcast_status_update", new_callable=AsyncMock)

    # Mockear SessionLocal para que devuelva la sesión de prueba
    mocker.patch("src.services.analysis_service.SessionLocal", return_value=db_session)
    
    # Mock GitHubService to avoid real instantiation
    mocker.patch("src.services.analysis_service.GitHubService")

    # Crear un repositorio de prueba en la base de datos en memoria
    repo = models.Repository(
        id=1,
        url="https://github.com/test/repo",
        name="test_repo",
        owner_id=1,
        status=AnalysisStatus.PENDING,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)
    repo_id = repo.id

    mock_repo_analysis = {
        "file_count": 10, "commit_count": 50, "languages": {"Python": 10000},
        "open_issues_count": 5, "open_pull_requests_count": 2,
        "contributors": [{"name": "contributor1"}], "tech_stack": ["Python"],
        "file_structure": [], "commit_history": []
    }
    mock_repository_analyzer.get_repository_analysis = AsyncMock(return_value=mock_repo_analysis)
    mock_generate_narratives_delay = mocker.patch("src.services.analysis_service.generate_narratives_task.delay")

    # No pasar 'db' directamente, dejar que la función use el SessionLocal mockeado
    analysis_service.clone_and_analyze_repository(repo_id)

    db_repo = db_session.query(models.Repository).filter(models.Repository.id == repo_id).first()
    assert db_repo.status == AnalysisStatus.COMPLETED

    mock_generate_narratives_delay.assert_called_once_with(repo_id, mock_repo_analysis)
    analysis_result = db_session.query(models.AnalysisResult).filter(models.AnalysisResult.repository_id == repo_id).first()
    assert analysis_result is not None
    assert analysis_result.file_count == 10

def test_clone_and_analyze_repository_not_found(db_session, mocker):
    repo_id = 999
    mock_logging_warning = mocker.patch("src.services.analysis_service.logging.warning")
    analysis_service.clone_and_analyze_repository(repo_id, db=db_session)
    mock_logging_warning.assert_called_once_with(f"Repository with ID {repo_id} not found.")

def test_clone_and_analyze_repository_exception(db_session, mock_repository_analyzer, mocker):
    mocker.patch("src.services.analysis_service._broadcast_status_update", new_callable=AsyncMock)
    mocker.patch("src.services.analysis_service.GitHubService")
    repo = models.Repository(url="https://github.com/test/repo", name="test_repo", owner_id=1, status=AnalysisStatus.PENDING)
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)
    repo_id = repo.id

    # Mockear la corrutina para que lance una excepción
    async def side_effect(*args, **kwargs):
        raise Exception("Test analysis error")
    mock_repository_analyzer.get_repository_analysis = side_effect

    analysis_service.clone_and_analyze_repository(repo_id, db=db_session)

    db_repo = db_session.query(models.Repository).filter(models.Repository.id == repo_id).first()
    assert db_repo.status == AnalysisStatus.FAILED
    assert "An unexpected error occurred" in db_repo.summary

def test_generate_narratives_task_success(db_session, mock_narrative_generator, mocker):
    repo = models.Repository(url="https://github.com/test/repo", name="test_repo", owner_id=1)
    db_session.add(repo)
    db_session.commit()
    analysis_result = models.AnalysisResult(repository_id=repo.id, summary="Old Summary", narrative="Old Narrative")
    db_session.add(analysis_result)
    db_session.commit()
    db_session.refresh(analysis_result)

    mock_repo_analysis = {"file_structure": [], "commit_history": []}
    mock_narrative_generator.generate_narrative.return_value = "New Narrative"
    mock_narrative_generator.generate_recruiter_summary = AsyncMock(return_value="New Summary")

    analysis_service.generate_narratives_task(repo.id, mock_repo_analysis, db=db_session)

    db_analysis_result = db_session.query(models.AnalysisResult).filter(models.AnalysisResult.id == analysis_result.id).first()
    assert db_analysis_result.narrative == "New Narrative"
    assert db_analysis_result.summary == "New Summary"

def test_generate_narratives_task_no_analysis_result(db_session, mock_narrative_generator, mocker):
    repo_id = 1
    mock_repo_analysis = {"some_data": "value"}
    mock_logging_warning = mocker.patch("src.services.analysis_service.logging.warning")

    analysis_service.generate_narratives_task(repo_id, mock_repo_analysis, db=db_session)

    mock_logging_warning.assert_called_once_with(f"AnalysisResult not found for repository ID {repo_id}. Cannot update narratives.")
    mock_narrative_generator.generate_narrative.assert_not_called()
    mock_narrative_generator.generate_recruiter_summary.assert_not_called()

def test_generate_narratives_task_exception(db_session, mock_narrative_generator, mocker):
    repo = models.Repository(url="https://github.com/test/repo", name="test_repo", owner_id=1)
    db_session.add(repo)
    db_session.commit()
    analysis_result = models.AnalysisResult(repository_id=repo.id)
    db_session.add(analysis_result)
    db_session.commit()

    mock_repo_analysis = {"some_data": "value"}
    mock_narrative_generator.generate_narrative.side_effect = Exception("Narrative generation error")
    mock_logging_error = mocker.patch("src.services.analysis_service.logging.error")

    analysis_service.generate_narratives_task(repo.id, mock_repo_analysis, db=db_session)

    mock_logging_error.assert_called_once()
