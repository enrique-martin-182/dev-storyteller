import asyncio

import pytest

from src.utils.async_utils import run_async
from src.utils.url_utils import extract_repo_name_from_url


@pytest.mark.parametrize("url, expected_name", [
    ("https://github.com/user/repo.git", "repo"),
    ("https://github.com/user/repo", "repo"),
    ("http://github.com/user/repo.git", "repo"),
    ("http://github.com/user/repo", "repo"),
    ("git@github.com:user/repo.git", "repo"),
    ("git@github.com:user/repo", "repo"),
    ("https://gitlab.com/user/group/repo.git", "repo"),
    ("https://bitbucket.org/user/repo.git", "repo"),
    ("https://github.com/user/repo/", "repo"),
    ("https://github.com/user/repo.git/", "repo"),
    ("", ""),
    ("not a url", "not a url"),
])
def test_extract_repo_name_from_url(url, expected_name):
    assert extract_repo_name_from_url(url) == expected_name

async def sample_coroutine():
    await asyncio.sleep(0.01)
    return "done"

@pytest.mark.asyncio
async def test_run_async_with_running_loop():
    # Test case where an event loop is already running
    result = run_async(sample_coroutine())
    assert asyncio.iscoroutine(result) or asyncio.isfuture(result)
    assert await result == "done"

def test_run_async_without_running_loop():
    # Test case where no event loop is running
    result = run_async(sample_coroutine())
    assert result == "done"
