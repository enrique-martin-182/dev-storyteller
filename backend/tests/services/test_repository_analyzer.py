from unittest.mock import MagicMock

import pytest

from src.services.github_service import GitHubService
from src.services.repository_analyzer import RepositoryAnalyzer


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

    mock_github_service.get_repository_commits.side_effect = [
        [ # For get_commit_history - first page
            {"sha": "hist_sha1", "commit": {"message": "History commit 1", "author": {"name": "user1", "date": "2024-01-01T00:00:00Z"}}},
            {"sha": "hist_sha2", "commit": {"message": "History commit 2", "author": {"name": "user2", "date": "2023-12-01T00:00:00Z"}}}
        ],
        [], # For get_commit_history - second page (signals end)
        [ # For get_file_structure - latest commit
            {"sha": "latest_sha", "commit": {"message": "Initial commit", "author": {"name": "user1", "date": "2024-01-01T00:00:00Z"}}}
        ]
    ]

    mock_github_service._make_request.return_value = {"tree": {"sha": "tree_sha"}}
    mock_github_service.get_git_tree.return_value = {"tree": [
        {"path": "file1.py", "type": "blob", "size": 100},
        {"path": "subdir", "type": "tree"},
        {"path": "subdir/file2.js", "type": "blob", "size": 50}
    ]}

    async def get_file_content_mock(_owner, _repo, file_name):
        if file_name == "requirements.txt":
            return "requests==2.28.1"
        elif file_name == "package.json":
            return '{"dependencies": {"react": "^18.2.0"}}'
        return "file content"

    mock_github_service.get_file_content.side_effect = get_file_content_mock

    # Act
    analysis = await analyzer.get_repository_analysis(github_url)

    # Assert
    assert analysis is not None
    assert analysis["repository_name"] == repo
    assert analysis["language"] == "Python"
    assert analysis["languages"] == {"Python": 100}
    assert "tech_stack" in analysis
    assert "React" in analysis["tech_stack"]
    assert "Requests" in analysis["tech_stack"]
    assert len(analysis["commit_history"]) == 2  # noqa: PLR2004
    assert analysis["commit_history"][0]["message"] == "History commit 1"
    assert "file_structure" in analysis
    assert len(analysis["file_structure"]) == 3  # noqa: PLR2004
    assert analysis["file_structure"][0]["path"] == "file1.py"
    assert "issues" in analysis
    assert len(analysis["issues"]) == 1
    assert analysis["issues"][0]["title"] == "Issue 1"
    assert "pull_requests" in analysis
    assert len(analysis["pull_requests"]) == 1
    assert analysis["pull_requests"][0]["title"] == "PR 1"
    assert "contributors" in analysis
    assert len(analysis["contributors"]) == 1
    assert analysis["contributors"][0]["login"] == "user1"

    mock_github_service.get_repository_details.assert_called_once_with(owner, repo)
    mock_github_service.get_repository_languages.assert_called_once_with(owner, repo)
    mock_github_service.get_repository_issues.assert_called_once_with(owner, repo)
    mock_github_service.get_repository_pulls.assert_called_once_with(owner, repo)
    mock_github_service.get_repository_contributors.assert_called_once_with(owner, repo)
    mock_github_service.get_repository_commits.assert_any_call(owner, repo, per_page=100, page=1)
    mock_github_service.get_git_tree.assert_called_once_with(owner, repo, "latest_sha", recursive=True)
    assert mock_github_service.get_file_content.call_count == 2  # noqa: PLR2004

@pytest.mark.asyncio
async def test_get_tech_stack_from_caching(mock_github_service):
    # Arrange
    analyzer = RepositoryAnalyzer(mock_github_service)
    owner = "test_owner"
    repo = "test_repo"
    github_url = f"https://github.com/{owner}/{repo}"

    async def get_file_content_mock(_owner, _repo, file_name):
        if file_name == "requirements.txt":
            return "flask==2.0.0\n# comment\ndjango>=3.0"
        if file_name == "package.json":
            return '{"dependencies": {"react": "18.2.0", "@angular/core": "~13.0.0"}}'
        if file_name == "pyproject.toml":
            return '[tool.poetry.dependencies]\npython = "^3.9"\nrequests = "^2.28.1"\n[tool.poetry.dev-dependencies]\npytest = "*"'
        if file_name == "Cargo.toml":
            return '[package]\nname = "my-rust-app"'
        return None

    mock_github_service.get_file_content.side_effect = get_file_content_mock

    # Act
    analysis = await analyzer.get_repository_analysis(github_url)

    expected_tech_stack = sorted([
        "Python/pip", "flask", "django",
        "Node.js/npm", "react", "@angular",
        "Python/Poetry/Flit", "requests", "pytest", "python",
        "Rust/Cargo"
    ])

    # Debugging print statements
    print(f"analysis['tech_stack']: {analysis['tech_stack']}")
    print(f"expected_tech_stack: {expected_tech_stack}")
    assert all(tech in analysis["tech_stack"] for tech in expected_tech_stack)


@pytest.mark.asyncio
async def test_get_commit_history_num_commits_break(mock_github_service):
    # Arrange
    analyzer = RepositoryAnalyzer(mock_github_service)
    owner = "test_owner"
    repo = "test_repo"
    num_commits = 1

    mock_github_service.get_repository_commits.side_effect = [
        [ # First page of commits
            {"sha": "hist_sha1", "commit": {"message": "History commit 1", "author": {"name": "user1", "date": "2024-01-01T00:00:00Z"}}},
            {"sha": "hist_sha2", "commit": {"message": "History commit 2", "author": {"name": "user2", "date": "2023-12-01T00:00:00Z"}}}
        ],
        [] # Second page (should not be called if break works)
    ]

    # Act
    commit_history = await analyzer.get_commit_history(owner, repo, num_commits=num_commits)

    # Assert
    assert len(commit_history) == num_commits
    assert mock_github_service.get_repository_commits.call_count == 1
    mock_github_service.get_repository_commits.assert_called_once_with(owner, repo, per_page=30, page=1)
