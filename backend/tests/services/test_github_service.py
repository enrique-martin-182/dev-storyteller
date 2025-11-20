import json
import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.core.exceptions import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
)
from src.services.github_service import GitHubService


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        yield

@pytest.fixture
def github_service():
    return GitHubService()

@pytest.fixture
def mock_async_client():
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client

@pytest.fixture
def mock_redis_client():
    with patch("redis.Redis") as mock_redis:
        yield mock_redis.return_value

@pytest.mark.asyncio
async def test_github_service_init_with_token():
    service = GitHubService(github_token="explicit_token")
    assert service.github_token == "explicit_token"
    assert "Authorization" in service.headers
    assert service.headers["Authorization"] == "token explicit_token"

@pytest.mark.asyncio
async def test_github_service_init_without_token_env_var():
    with patch.dict(os.environ, {}, clear=True), pytest.raises(ValueError, match="GitHub token not provided and GITHUB_TOKEN environment variable not set."):
        GitHubService()

@pytest.mark.asyncio
async def test_github_service_init_with_env_var():
    service = GitHubService()
    assert service.github_token == "test_token"
    assert "Authorization" in service.headers
    assert service.headers["Authorization"] == "token test_token"

@pytest.mark.asyncio
async def test_make_request_success(mock_async_client, mock_redis_client, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response

    mock_redis_client.get.return_value = None # No cached response

    response = await github_service._make_request("GET", "/test")
    assert response == {"data": "test"}
    mock_redis_client.setex.assert_called_once()

@pytest.mark.asyncio
async def test_make_request_cached_response(mock_async_client, mock_redis_client, github_service):
    mock_redis_client.get.return_value = json.dumps({"data": "cached"})

    response = await github_service._make_request("GET", "/test")
    assert response == {"data": "cached"}
    mock_async_client.return_value.__aenter__.return_value.request.assert_not_called()
    mock_redis_client.get.assert_called_once()
    mock_redis_client.setex.assert_not_called()

@pytest.mark.asyncio
async def test_make_request_github_auth_error(mock_async_client, mock_redis_client, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.headers = {}
    mock_response.json.return_value = {} # Add this line
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=httpx.Request("GET", "http://test.com"), response=mock_response
    )
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None # Ensure no cached response

    with pytest.raises(GitHubAuthError):
        await github_service._make_request("GET", "/test")

@pytest.mark.asyncio
async def test_make_request_github_rate_limit_error(mock_async_client, mock_redis_client, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 403
    mock_response.text = "Rate Limit Exceeded"
    mock_response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "12345"}
    mock_response.json.return_value = {} # Add this line
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=httpx.Request("GET", "http://test.com"), response=mock_response
    )
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None # Ensure no cached response

    with pytest.raises(GitHubRateLimitError):
        await github_service._make_request("GET", "/test")

@pytest.mark.asyncio
async def test_make_request_github_resource_not_found_error(mock_async_client, mock_redis_client, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.headers = {}
    mock_response.json.return_value = {} # Add this line
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=httpx.Request("GET", "http://test.com"), response=mock_response
    )
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None # Ensure no cached response

    with pytest.raises(GitHubResourceNotFoundError):
        await github_service._make_request("GET", "/test")

@pytest.mark.asyncio
async def test_make_request_github_api_error(mock_async_client, mock_redis_client, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Server Error"
    mock_response.headers = {}
    mock_response.json.return_value = {} # Add this line
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=httpx.Request("GET", "http://test.com"), response=mock_response
    )
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None # Ensure no cached response

    with pytest.raises(GitHubAPIError):
        await github_service._make_request("GET", "/test")

@pytest.mark.asyncio
async def test_get_repository_details(mock_async_client, mock_redis_client, github_service):
    mock_response_data = {"name": "repo", "description": "desc"}
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    details = await github_service.get_repository_details("owner", "repo")
    assert details == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo"
    )

@pytest.mark.asyncio
async def test_get_repository_content(mock_async_client, mock_redis_client, github_service):
    mock_response_data = [{"name": "file.txt"}]
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    content = await github_service.get_repository_content("owner", "repo", "path")
    assert content == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/contents/path"
    )

@pytest.mark.asyncio
async def test_get_repository_commits(mock_async_client, mock_redis_client, github_service):
    mock_response_data = [{"sha": "123", "commit": {"message": "Initial commit"}}]
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    commits = await github_service.get_repository_commits("owner", "repo", per_page=10, page=2)
    assert commits == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/commits?per_page=10&page=2"
    )

@pytest.mark.asyncio
async def test_get_repository_issues(mock_async_client, mock_redis_client, github_service):
    mock_response_data = [{"id": 1, "title": "Bug"}]
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    issues = await github_service.get_repository_issues("owner", "repo", state="closed")
    assert issues == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/issues?state=closed"
    )

@pytest.mark.asyncio
async def test_get_repository_pulls(mock_async_client, mock_redis_client, github_service):
    mock_response_data = [{"id": 1, "title": "Feature"}]
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    pulls = await github_service.get_repository_pulls("owner", "repo", state="all")
    assert pulls == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/pulls?state=all"
    )

@pytest.mark.asyncio
async def test_get_repository_contributors(mock_async_client, mock_redis_client, github_service):
    mock_response_data = [{"login": "contributor1"}]
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    contributors = await github_service.get_repository_contributors("owner", "repo")
    assert contributors == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/contributors"
    )

@pytest.mark.asyncio
async def test_get_git_tree(mock_async_client, mock_redis_client, github_service):
    mock_response_data = {"sha": "abc", "tree": []}
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    tree = await github_service.get_git_tree("owner", "repo", "sha123")
    assert tree == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/git/trees/sha123?recursive=1"
    )

@pytest.mark.asyncio
async def test_get_repository_languages(mock_async_client, mock_redis_client, github_service):
    mock_response_data = {"Python": 10000, "JavaScript": 5000}
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    languages = await github_service.get_repository_languages("owner", "repo")
    assert languages == mock_response_data
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/languages"
    )

@pytest.mark.asyncio
async def test_get_file_content_success(mock_async_client, mock_redis_client, github_service):
    encoded_content = "SGVsbG8gV29ybGQ=" # "Hello World" base64 encoded
    mock_response_data = {"content": encoded_content, "encoding": "base64"}
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    content = await github_service.get_file_content("owner", "repo", "file.txt")
    assert content == "Hello World"
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/contents/file.txt"
    )

@pytest.mark.asyncio
async def test_get_file_content_not_found(mock_async_client, mock_redis_client, github_service):
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.headers = {}
    mock_response.json.return_value = {} # Add this line
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=httpx.Request("GET", "http://test.com"), response=mock_response
    )
    mock_async_client.return_value.__aenter__.return_value.request.return_value = mock_response
    mock_redis_client.get.return_value = None

    content = await github_service.get_file_content("owner", "repo", "non_existent_file.txt")
    assert content is None
    mock_async_client.return_value.__aenter__.return_value.request.assert_called_once_with(
        "GET", "https://api.github.com/repos/owner/repo/contents/non_existent_file.txt"
    )
