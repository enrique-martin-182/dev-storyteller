import json
from unittest.mock import AsyncMock, patch

import pytest

from src.services.github_service import GitHubService
from src.services.repository_analyzer import RepositoryAnalyzer

EXPECTED_FILE_STRUCTURE_COUNT = 2
EXPECTED_COMMIT_CALL_COUNT = 2
EXPECTED_ANALYSIS_COMMIT_COUNT = 2

@pytest.fixture
def mock_github_service():
    return AsyncMock(spec=GitHubService)

@pytest.fixture
def repository_analyzer(mock_github_service):
    return RepositoryAnalyzer(github_service=mock_github_service)

def test_repository_analyzer_init(mock_github_service):
    analyzer = RepositoryAnalyzer(github_service=mock_github_service)
    assert analyzer.github_service == mock_github_service

@pytest.mark.asyncio
async def test_get_file_structure_success(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    mock_github_service.get_repository_commits.return_value = [
        {"sha": "commit_sha_1", "commit": {"tree": {"sha": "tree_sha_1"}}}
    ]
    mock_github_service._make_request.return_value = {"tree": {"sha": "tree_sha_1"}}
    mock_github_service.get_git_tree.return_value = {
        "tree": [
            {"path": "file1.txt", "type": "blob", "size": 100},
            {"path": "dir1", "type": "tree"},
        ]
    }

    file_structure = await repository_analyzer.get_file_structure(owner, repo)

    mock_github_service.get_repository_commits.assert_called_once_with(owner, repo)
    mock_github_service._make_request.assert_called_once_with("GET", f"/repos/{owner}/{repo}/git/commits/commit_sha_1")
    mock_github_service.get_git_tree.assert_called_once_with(owner, repo, "tree_sha_1")
    assert len(file_structure) == EXPECTED_FILE_STRUCTURE_COUNT
    assert file_structure[0]["path"] == "file1.txt"
    assert file_structure[1]["type"] == "tree"

@pytest.mark.asyncio
async def test_get_file_structure_no_commits(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    mock_github_service.get_repository_commits.return_value = []

    file_structure = await repository_analyzer.get_file_structure(owner, repo)

    mock_github_service.get_repository_commits.assert_called_once_with(owner, repo)
    mock_github_service._make_request.assert_not_called()
    mock_github_service.get_git_tree.assert_not_called()
    assert file_structure == []

@pytest.mark.asyncio
async def test_get_commit_history_multiple_pages(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    num_commits = 50
    mock_github_service.get_repository_commits.side_effect = [
        [{"sha": f"sha{i}", "commit": {"message": f"Commit {i}", "author": {"name": "Author", "date": "date"}}} for i in range(30)],
        [{"sha": f"sha{i}", "commit": {"message": f"Commit {i}", "author": {"name": "Author", "date": "date"}}} for i in range(30, 50)],
        [] # End of commits
    ]

    commit_history = await repository_analyzer.get_commit_history(owner, repo, num_commits)

    assert len(commit_history) == num_commits
    assert mock_github_service.get_repository_commits.call_count == EXPECTED_COMMIT_CALL_COUNT
    assert commit_history[0]["message"] == "Commit 0"
    assert commit_history[49]["message"] == "Commit 49"

@pytest.mark.asyncio
async def test_get_commit_history_no_commits(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    mock_github_service.get_repository_commits.return_value = []

    commit_history = await repository_analyzer.get_commit_history(owner, repo, num_commits=10)

    mock_github_service.get_repository_commits.assert_called_once_with(owner, repo, per_page=30, page=1)
    assert commit_history == []

@pytest.mark.asyncio
async def test_get_repository_analysis_success(repository_analyzer, mock_github_service):
    owner, repo_name = "test_owner", "test_repo"
    github_url = f"https://github.com/{owner}/{repo_name}"

    mock_github_service.get_repository_details.return_value = {
        "name": repo_name, "description": "Test Repo", "language": "Python"
    }
    mock_github_service.get_repository_languages.return_value = {"Python": 10000}
    mock_github_service.get_repository_issues.return_value = [{"id": 1}]
    mock_github_service.get_repository_pulls.return_value = [{"id": 2}]
    mock_github_service.get_repository_contributors.return_value = [{"login": "dev1"}]
    mock_github_service.get_repository_commits.side_effect = [
        [{"sha": "c1"}], [{"sha": "c2"}], []
    ]
    with patch("src.utils.url_utils.parse_github_url", return_value=(owner, repo_name)), \
         patch.object(repository_analyzer, "get_file_structure", new_callable=AsyncMock) as mock_get_file_structure, \
         patch.object(repository_analyzer, "_identify_tech_stack", new_callable=AsyncMock) as mock_identify_tech_stack:

        mock_get_file_structure.return_value = [{"path": "file1.txt"}]
        mock_identify_tech_stack.return_value = ["Python", "FastAPI"]

        analysis = await repository_analyzer.get_repository_analysis(github_url)

        # No need to assert parse_github_url directly as it's mocked at the module level
        # parse_github_url.assert_called_once_with(github_url) # This would be if we imported it directly in the test
        mock_github_service.get_repository_details.assert_called_once_with(owner, repo_name)
        mock_github_service.get_repository_languages.assert_called_once_with(owner, repo_name)
        mock_github_service.get_repository_issues.assert_called_once_with(owner, repo_name)
        mock_github_service.get_repository_pulls.assert_called_once_with(owner, repo_name)
        mock_github_service.get_repository_contributors.assert_called_once_with(owner, repo_name)
        assert mock_github_service.get_repository_commits.call_count == 3
        mock_get_file_structure.assert_called_once_with(owner, repo_name)
        mock_identify_tech_stack.assert_called_once_with(owner, repo_name)

        assert analysis["name"] == repo_name
        assert analysis["description"] == "Test Repo"
        assert analysis["main_language"] == "Python"
        assert analysis["owner"] == owner
        assert analysis["repo_name"] == repo_name
        assert analysis["languages"] == {"Python": 10000}
        assert analysis["file_count"] == 1
        assert analysis["commit_count"] == EXPECTED_ANALYSIS_COMMIT_COUNT
        assert analysis["open_issues_count"] == 1
        assert analysis["open_pull_requests_count"] == 1
        assert analysis["contributors"] == ["dev1"]
        assert analysis["file_structure"] == [{"path": "file1.txt"}]
        assert analysis["tech_stack"] == ["Python", "FastAPI"]

@pytest.mark.asyncio
async def test_identify_tech_stack_package_json(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    mock_github_service.get_file_content.side_effect = [
        json.dumps({"dependencies": {"express": "^4.17.1", "@angular/core": "~12.0.0"}}), # package.json
        None, # requirements.txt
        None, # pom.xml
        None, # build.gradle
        None, # go.mod
        None, # Cargo.toml
        None, # composer.json
        None, # Gemfile
        None, # mix.exs
        None, # cabal.project
        None, # stack.yaml
        None, # project.clj
        None, # deps.edn
        None, # pyproject.toml
        None, # webpack.config.js
        None, # vite.config.js
        None, # next.config.js
        None, # angular.json
        None, # tsconfig.json
        None, # tailwind.config.js
        None, # package-lock.json
        None, # yarn.lock
        None, # pnpm-lock.yaml
    ]

    tech_stack = await repository_analyzer._identify_tech_stack(owner, repo)

    assert "Node.js/npm" in tech_stack
    assert "express" in tech_stack
    assert "@angular" in tech_stack
    assert "Python/pip" not in tech_stack # Ensure other tech is not added
    assert mock_github_service.get_file_content.call_count > 0

@pytest.mark.asyncio
async def test_identify_tech_stack_requirements_txt(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    mock_github_service.get_file_content.side_effect = [
        None, # package.json
        "fastapi==0.68.0\npytest>=6.2.5\n-r requirements-dev.txt", # requirements.txt
        None, # pom.xml
        None, # build.gradle
        None, # go.mod
        None, # Cargo.toml
        None, # composer.json
        None, # Gemfile
        None, # mix.exs
        None, # cabal.project
        None, # stack.yaml
        None, # project.clj
        None, # deps.edn
        None, # pyproject.toml
        None, # webpack.config.js
        None, # vite.config.js
        None, # next.config.js
        None, # angular.json
        None, # tsconfig.json
        None, # tailwind.config.js
        None, # package-lock.json
        None, # yarn.lock
        None, # pnpm-lock.yaml
    ]

    tech_stack = await repository_analyzer._identify_tech_stack(owner, repo)

    assert "Python/pip" in tech_stack
    assert "fastapi" in tech_stack
    assert "pytest" in tech_stack
    assert "express" not in tech_stack
    assert mock_github_service.get_file_content.call_count > 0

@pytest.mark.asyncio
async def test_identify_tech_stack_no_tech_files(repository_analyzer, mock_github_service):
    owner, repo = "test_owner", "test_repo"
    mock_github_service.get_file_content.return_value = None # No tech files found

    tech_stack = await repository_analyzer._identify_tech_stack(owner, repo)

    assert tech_stack == []
    assert mock_github_service.get_file_content.call_count > 0
