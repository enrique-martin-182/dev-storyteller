import pytest

from src.utils.url_utils import extract_repo_name_from_url, parse_github_url


# Tests for extract_repo_name_from_url
@pytest.mark.parametrize(
    "url, expected_repo_name",
    [
        ("https://github.com/owner/repo_name", "repo_name"),
        ("https://github.com/owner/repo_name.git", "repo_name"),
        ("https://github.com/owner/sub/repo_name", "repo_name"),
        ("https://github.com/repo_name", "repo_name"),
        ("https://api.github.com/repos/owner/repo_name", "repo_name"),
        ("http://localhost/owner/repo_name", "repo_name"),
        ("https://github.com/", ""),
        ("https://github.com", ""),
        ("", ""),
    ],
)
def test_extract_repo_name_from_url(url, expected_repo_name):
    assert extract_repo_name_from_url(url) == expected_repo_name


# Tests for parse_github_url
@pytest.mark.parametrize(
    "url, expected_owner, expected_repo_name",
    [
        ("https://github.com/owner/repo_name", "owner", "repo_name"),
        ("https://github.com/owner/repo_name.git", "owner", "repo_name"),
        ("https://github.com/owner/another_repo", "owner", "another_repo"),
    ],
)
def test_parse_github_url_success(url, expected_owner, expected_repo_name):
    owner, repo_name = parse_github_url(url)
    assert owner == expected_owner
    assert repo_name == expected_repo_name


@pytest.mark.parametrize(
    "url, expected_error_message",
    [
        ("https://gitlab.com/owner/repo_name", "Invalid GitHub URL: Host is not github.com in https://gitlab.com/owner/repo_name"),
        ("https://github.com/owner", "Invalid GitHub URL format: https://github.com/owner"),
        ("https://github.com/", "Invalid GitHub URL format: https://github.com/"),
        ("invalid-url", "Invalid GitHub URL: Host is not github.com in invalid-url"),
        ("", "Invalid GitHub URL: Host is not github.com in "),
    ],
)
def test_parse_github_url_invalid(url, expected_error_message):
    with pytest.raises(ValueError) as excinfo:
        parse_github_url(url)
    assert str(excinfo.value) == expected_error_message