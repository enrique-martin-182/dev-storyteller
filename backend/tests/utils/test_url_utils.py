import pytest

from src.utils.url_utils import extract_repo_name_from_url, parse_github_url


# Tests for extract_repo_name_from_url
@pytest.mark.parametrize("url, expected_name", [
    ("https://github.com/owner/repo_name.git", "repo_name"),
    ("https://github.com/owner/repo_name", "repo_name"),
    ("http://gitlab.com/group/subgroup/another_repo.git", "another_repo"),
    ("https://bitbucket.org/project/my_repo", "my_repo"),
    ("https://github.com/owner/repo_name/", "repo_name"), # Trailing slash
    ("https://github.com/repo_name.git", "repo_name"), # No owner
    ("https://github.com/repo_name", "repo_name"), # No owner and no .git
    ("https://github.com/", ""), # Root URL
    ("", ""), # Empty URL
    ("ftp://some.server.com/path/to/file.zip", "file.zip"), # Non-git URL
])
def test_extract_repo_name_from_url(url, expected_name):
    assert extract_repo_name_from_url(url) == expected_name


# Tests for parse_github_url
@pytest.mark.parametrize("url, expected_owner, expected_repo_name", [
    ("https://github.com/owner/repo_name.git", "owner", "repo_name"),
    ("https://github.com/owner/repo_name", "owner", "repo_name"),
    ("https://github.com/octocat/Spoon-Knife.git", "octocat", "Spoon-Knife"),
    ("https://github.com/octocat/Spoon-Knife", "octocat", "Spoon-Knife"),
    ("https://github.com/owner/repo_name/", "owner", "repo_name"), # Trailing slash
])
def test_parse_github_url_valid(url, expected_owner, expected_repo_name):
    owner, repo_name = parse_github_url(url)
    assert owner == expected_owner
    assert repo_name == expected_repo_name


@pytest.mark.parametrize("url", [
    "https://github.com/repo_name.git", # Missing owner
    "https://github.com/owner", # Missing repo name
    "https://github.com/", # Root URL
    "", # Empty URL
    "invalid-url", # Malformed URL
    "http://example.com/not_github/repo", # Non-github URL
])
def test_parse_github_url_invalid(url):
    with pytest.raises(ValueError):
        parse_github_url(url)