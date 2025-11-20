import base64
import json
import os

import httpx
import redis
from httpx import codes

from src.core.exceptions import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
)


class GitHubService:
    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token not provided and GITHUB_TOKEN environment variable not set.")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0) # Initialize Redis client
        self.cache_ttl = 300 # Cache time-to-live in seconds (5 minutes)

    async def _make_request(self, method: str, url: str, **kwargs):
        cache_key = f"github:{method}:{url}:{json.dumps(kwargs, sort_keys=True)}"
        cached_response = self.redis_client.get(cache_key)
        if cached_response:
            return json.loads(cached_response)

        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.request(method, f"{self.base_url}{url}", **kwargs)
            json_response = None # Initialize json_response
            try:
                await response.raise_for_status()
                json_response = await response.json()
                if json_response is not None: # Only cache if response was successful and json_response is not None
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(json_response))
                return json_response
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [401, 403]:
                    if 'X-RateLimit-Remaining' in e.response.headers and int(e.response.headers['X-RateLimit-Remaining']) == 0:
                        reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
                        raise GitHubRateLimitError(
                            f"GitHub API rate limit exceeded. Resets at {reset_time}.",
                            status_code=e.response.status_code,
                            headers=dict(e.response.headers),
                            reset_time=reset_time
                        ) from e
                    raise GitHubAuthError(
                        f"Authentication failed or forbidden: {e.response.text}",
                        status_code=e.response.status_code,
                        headers=dict(e.response.headers)
                    ) from e
                elif e.response.status_code == codes.NOT_FOUND:
                    raise GitHubResourceNotFoundError(
                        f"GitHub resource not found: {e.response.text}",
                        status_code=e.response.status_code,
                        headers=dict(e.response.headers)
                    ) from e
                else:
                    raise GitHubAPIError(
                        f"GitHub API error: {e.response.text}",
                        status_code=e.response.status_code,
                        headers=dict(e.response.headers)
                    ) from e

    async def get_repository_details(self, owner: str, repo: str):
        """
        Fetches detailed information about a GitHub repository, including name, description, and languages.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}")

    async def get_repository_content(self, owner: str, repo: str, path: str = ""):
        """
        Fetches the content of a directory or file in a GitHub repository.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}")

    async def get_repository_commits(self, owner: str, repo: str, per_page: int = 30, page: int = 1):
        """
        Fetches the commit history for a GitHub repository with pagination.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/commits?per_page={per_page}&page={page}")

    async def get_repository_issues(self, owner: str, repo: str, state: str = "open"):
        """
        Fetches issues for a GitHub repository.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/issues?state={state}")

    async def get_repository_pulls(self, owner: str, repo: str, state: str = "open"):
        """
        Fetches pull requests for a GitHub repository.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/pulls?state={state}")

    async def get_repository_contributors(self, owner: str, repo: str):
        """
        Fetches contributors for a GitHub repository.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/contributors")

    async def get_git_tree(self, owner: str, repo: str, sha: str):
        """
        Fetches the Git tree for a GitHub repository, recursively.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")

    async def get_repository_languages(self, owner: str, repo: str) -> dict:
        """
        Fetches detailed language statistics for a GitHub repository.
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}/languages")

    async def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        """
        Fetches the content of a specific file from a GitHub repository.
        """
        try:
            response = await self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}")
            if response and "content" in response and "encoding" in response:
                if response["encoding"] == "base64":
                    return base64.b64decode(response["content"]).decode("utf-8")
                return response["content"]
            return None
        except GitHubResourceNotFoundError:
            return None

