
import pytest
from src.utils.url_utils import extract_repo_name_from_url, parse_github_url

@pytest.mark.parametrize("url, expected", [
    ("https://github.com/user/repo.git", "repo"),
    ("https://github.com/user/repo", "repo"),
    ("http://github.com/user/repo.git", "repo"),
    ("http://github.com/user/repo", "repo"),
    ("https://gitlab.com/user/repo", "repo"),
])
def test_extract_repo_name_from_url(url, expected):
    assert extract_repo_name_from_url(url) == expected

@pytest.mark.parametrize("url, expected_owner, expected_repo", [
    ("https://github.com/user/repo.git", "user", "repo"),
    ("https://github.com/user/repo", "user", "repo"),
    ("http://github.com/user/repo.git", "user", "repo"),
    ("http://github.com/user/repo", "user", "repo"),
])
def test_parse_github_url(url, expected_owner, expected_repo):
    owner, repo = parse_github_url(url)
    assert owner == expected_owner
    assert repo == expected_repo

@pytest.mark.parametrize("url", [
    "https://gitlab.com/user/repo",
    "https://github.com/user",
    "https://github.com/",
])
def test_parse_github_url_invalid(url):
    with pytest.raises(ValueError):
        parse_github_url(url)
