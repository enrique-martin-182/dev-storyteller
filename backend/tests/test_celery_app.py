from unittest.mock import MagicMock

import pytest
from celery import Celery

# Import the module under test using a relative import
# to allow mocking of global variables like os.getenv
from src import celery_app as celery_app_module


@pytest.fixture
def clean_env_celery(monkeypatch):
    """Fixture to ensure a clean environment for each test."""
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND_URL", raising=False)


def test_celery_app_instance():
    celery_app = celery_app_module.get_celery_app()
    assert isinstance(celery_app, Celery)
    assert celery_app.main == 'dev_storyteller'


def test_celery_broker_url_default():
    celery_app = celery_app_module.get_celery_app()
    assert celery_app.conf.broker_url == 'redis://localhost:6379/0'
    assert celery_app.conf.result_backend == 'redis://localhost:6379/0'


def test_celery_broker_url_from_env(monkeypatch, mocker):
    test_broker_url = "redis://test_broker:1234/1"
    test_backend_url = "redis://test_backend:5678/2"
    monkeypatch.setenv("CELERY_BROKER_URL", test_broker_url)
    monkeypatch.setenv("CELERY_RESULT_BACKEND_URL", test_backend_url)

    # Patch the Celery class itself to control its instantiation
    mock_celery_class = mocker.patch('src.celery_app.Celery')
    mock_celery_instance = MagicMock()
    mock_celery_class.return_value = mock_celery_instance

    # Mock the .conf attribute to return a MagicMock object for its attributes
    mock_celery_instance.conf = MagicMock()
    mock_celery_instance.conf.task_track_started = True
    mock_celery_instance.conf.result_backend = test_backend_url
    mock_celery_instance.conf.broker_url = test_broker_url


    # When get_celery_app is called, it will use our mocked Celery class
    celery_app_module.get_celery_app()

    # Assert that Celery was instantiated with the correct broker and backend URLs
    mock_celery_class.assert_called_once_with(
        'dev_storyteller',
        broker=test_broker_url,
        backend=test_backend_url,
        include=['src.services.analysis_service']
    )
    # Also assert the configurations applied to the mock instance
    mock_celery_instance.conf.update.assert_called_once()
    assert mock_celery_instance.conf.task_track_started is True
    assert mock_celery_instance.conf.result_backend == test_backend_url
    assert mock_celery_instance.conf.broker_url == test_broker_url


def test_celery_app_config():
    celery_app = celery_app_module.get_celery_app()
    assert celery_app.conf.task_track_started is True
    assert celery_app.conf.task_serializer == 'json'
    assert celery_app.conf.result_serializer == 'json'
    assert celery_app.conf.accept_content == ['json']
    assert celery_app.conf.timezone == 'UTC'
    assert celery_app.conf.enable_utc is True


def test_celery_app_includes_tasks():
    celery_app = celery_app_module.get_celery_app()
    assert 'src.services.analysis_service' in celery_app.conf.include
