import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.repository_analyzer import RepositoryAnalyzer
from src.services.github_service import GitHubService

@pytest.fixture
def mock_github_service():
    return MagicMock(spec=GitHubService)

@pytest.mark.asyncio
async def test_get_repository_analysis(mock_github_service):
    # Arrange
    analyzer = RepositoryAnalyzer(mock_github_service)
    owner = "test_owner"
    repo = "test_repo"
    github_url = f"https://github.com/{owner}/{repo}"

    mock_github_service.get_repository_details.return_value = {"name": repo, "language": "Python"}
    mock_github_service.get_repository_languages.return_value = {"Python": 100}
    mock_github_service.get_repository_issues.return_value = [{"title": "Issue 1"}]
    mock_github_service.get_repository_pulls.return_value = [{"title": "PR 1"}]
    mock_github_service.get_repository_contributors.return_value = [{"login": "user1"}]
    async def get_file_content_mock(owner, repo, file_path):
        if file_path == "requirements.txt":
            return "flask"
        if file_path == "package.json":
            return '{"dependencies": {"react": "18.2.0"}}'
        return None

    mock_github_service.get_file_content.side_effect = get_file_content_mock
    mock_github_service.get_repository_commits.side_effect = StopAsyncIteration

    # Act
    analysis = await analyzer.get_repository_analysis(github_url)

    # Assert
    assert analysis["name"] == repo
    assert analysis["main_language"] == "Python"
    assert analysis["languages"] == {"Python": 100}
    assert analysis["open_issues_count"] == 1
    assert analysis["open_pull_requests_count"] == 1
    assert analysis["contributors"] == ["user1"]
    assert analysis["commit_count"] == 0
    assert analysis["file_count"] == 0
    assert analysis["file_structure"] == []
    assert "Python/pip" in analysis["tech_stack"]
    assert "flask" in analysis["tech_stack"]