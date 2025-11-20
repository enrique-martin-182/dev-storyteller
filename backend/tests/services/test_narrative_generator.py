from unittest.mock import AsyncMock, patch

import pytest

# Keep import at module level for MAX_SUMMARY_LENGTH
from src.services.narrative_generator import MAX_SUMMARY_LENGTH, NarrativeGenerator

# from src.db.database import GEMINI_API_KEY # No longer needed to import directly here

@pytest.fixture
def mock_generative_model(mocker):
    # Mock the GenerativeModel class itself
    mock_model_class = mocker.patch("google.generativeai.GenerativeModel", autospec=True)
    # Mock the instance that would be returned when GenerativeModel is called
    mock_instance = mock_model_class.return_value
    # Mock the generate_content method on the instance
    mock_instance.generate_content.return_value.text = "Mocked LLM response"
    mock_instance.generate_content_async.return_value = AsyncMock(text="Mocked LLM async response")
    return mock_model_class # Yield the mocked class

@pytest.fixture
def narrative_generator(mock_generative_model): # Now mock_generative_model is the mocked class
    # Patch GEMINI_API_KEY to avoid the initial check in the constructor
    with patch("src.services.narrative_generator.GEMINI_API_KEY", new="test_api_key"), \
         patch("google.generativeai.configure", autospec=True): # Mock genai.configure
        yield NarrativeGenerator()

def test_narrative_generator_init_no_api_key():
    # Patch GEMINI_API_KEY in the module where it's used
    with patch("src.services.narrative_generator.GEMINI_API_KEY", new=None), pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
        NarrativeGenerator()

def test_generate_narrative_success(narrative_generator, mock_generative_model):
    repo_details = {
        "name": "test_repo",
        "description": "A test repository",
        "main_language": "Python",
        "languages": {"Python": 100},
        "tech_stack": ["Python", "FastAPI"],
        "topics": ["testing"],
        "license": "MIT",
        "stargazers_count": 10,
        "forks_count": 5,
        "open_issues_count": 2,
        "open_pull_requests_count": 1,
        "contributors": ["dev1", "dev2"],
        "file_count": 20,
        "commit_count": 50,
        "file_structure": [{"path": "src/main.py"}],
        "commit_history": [{"message": "Initial commit", "author_name": "dev1", "date": "2023-01-01"}],
    }
    expected_narrative = "This is a comprehensive narrative."
    narrative_generator.model.generate_content.return_value.text = expected_narrative
    narrative = narrative_generator.generate_narrative(repo_details)
    assert narrative == expected_narrative
    narrative_generator.model.generate_content.assert_called_once()

def test_generate_narrative_exception(narrative_generator, mock_generative_model):
    repo_details = {}
    narrative_generator.model.generate_content.side_effect = Exception("LLM error")
    narrative = narrative_generator.generate_narrative(repo_details)
    assert narrative == "Error generating narrative."
    narrative_generator.model.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_generate_recruiter_summary_success(narrative_generator, mock_generative_model):
    repo_analysis = {
        "name": "test_repo",
        "description": "A test repository",
        "main_language": "Python",
        "languages": {"Python": 100},
        "tech_stack": ["Python", "FastAPI"],
        "topics": ["testing"],
        "stargazers_count": 10,
        "forks_count": 5,
        "open_issues_count": 2,
        "open_pull_requests_count": 1,
        "contributors": ["dev1", "dev2"],
        "file_count": 20,
        "commit_count": 50,
    }
    expected_summary = "This is a concise summary for recruiters."
    narrative_generator.model.generate_content_async.return_value.text = expected_summary
    summary = await narrative_generator.generate_recruiter_summary(repo_analysis)
    assert summary == expected_summary
    narrative_generator.model.generate_content_async.assert_called_once()

@pytest.mark.asyncio
async def test_generate_recruiter_summary_truncation(narrative_generator, mock_generative_model):
    repo_analysis = {}
    long_summary = "A" * (MAX_SUMMARY_LENGTH + 50)
    narrative_generator.model.generate_content_async.return_value.text = long_summary
    summary = await narrative_generator.generate_recruiter_summary(repo_analysis)
    assert len(summary) == MAX_SUMMARY_LENGTH
    assert summary.endswith("...")
    narrative_generator.model.generate_content_async.assert_called_once()

@pytest.mark.asyncio
async def test_generate_recruiter_summary_exception(narrative_generator, mock_generative_model):
    repo_analysis = {}
    narrative_generator.model.generate_content_async.side_effect = Exception("LLM error")
    summary = await narrative_generator.generate_recruiter_summary(repo_analysis)
    assert summary == "Error generating recruiter summary."
    narrative_generator.model.generate_content_async.assert_called_once()
