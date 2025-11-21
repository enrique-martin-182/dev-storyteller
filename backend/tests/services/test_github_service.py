
import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.services.github_service import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
    GitHubService,
)


class TestGitHubService(unittest.TestCase):

    @patch('os.getenv')
    def test_init_with_token(self, mock_getenv):
        mock_getenv.return_value = 'test_token'
        service = GitHubService()
        self.assertEqual(service.github_token, 'test_token')

    @patch('os.getenv')
    def test_init_without_token(self, mock_getenv):
        mock_getenv.return_value = None
        with self.assertRaises(ValueError):
            GitHubService()

    @patch('redis.Redis')
    def test_make_request_cached(self, mock_redis):
        mock_redis.return_value.get.return_value = json.dumps({'data': 'cached'})
        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            response = await service._make_request('GET', '/test')
            self.assertEqual(response, {'data': 'cached'})
            mock_redis.return_value.get.assert_called_once()

        asyncio.run(run_test())

    @patch('redis.Redis')
    @patch('httpx.AsyncClient')
    def test_make_request_uncached(self, mock_async_client, mock_redis):
        mock_redis.return_value.get.return_value = None
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={'data': 'live'})
        mock_response.raise_for_status = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            response = await service._make_request('GET', '/test')
            self.assertEqual(response, {'data': 'live'})
            mock_redis.return_value.setex.assert_called_once()

        asyncio.run(run_test())

    @patch('redis.Redis')
    @patch('httpx.AsyncClient')
    def test_make_request_rate_limit_error(self, mock_async_client, mock_redis):
        mock_redis.return_value.get.return_value = None
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.headers = {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '123'}
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("...", request=MagicMock(), response=mock_response))
        mock_async_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            with self.assertRaises(GitHubRateLimitError):
                await service._make_request('GET', '/test')

        asyncio.run(run_test())

    @patch('redis.Redis')
    @patch('httpx.AsyncClient')
    def test_make_request_auth_error(self, mock_async_client, mock_redis):
        mock_redis.return_value.get.return_value = None
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Authentication failed"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("...", request=MagicMock(), response=mock_response))
        mock_async_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            with self.assertRaises(GitHubAuthError):
                await service._make_request('GET', '/test')

        asyncio.run(run_test())

    @patch('redis.Redis')
    @patch('httpx.AsyncClient')
    def test_make_request_not_found_error(self, mock_async_client, mock_redis):
        mock_redis.return_value.get.return_value = None
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("...", request=MagicMock(), response=mock_response))
        mock_async_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            with self.assertRaises(GitHubResourceNotFoundError):
                await service._make_request('GET', '/test')

        asyncio.run(run_test())

    @patch('redis.Redis')
    @patch('httpx.AsyncClient')
    def test_make_request_api_error(self, mock_async_client, mock_redis):
        mock_redis.return_value.get.return_value = None
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.text = "API Error"
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("...", request=MagicMock(), response=mock_response))
        mock_async_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            with self.assertRaises(GitHubAPIError):
                await service._make_request('GET', '/test')

        asyncio.run(run_test())

    def test_get_repository_details(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value={'name': 'test-repo'})

        async def run_test():
            response = await service.get_repository_details('owner', 'repo')
            self.assertEqual(response['name'], 'test-repo')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo')

        asyncio.run(run_test())

    def test_get_repository_content(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value=[{'name': 'file.py'}])

        async def run_test():
            response = await service.get_repository_content('owner', 'repo', 'path')
            self.assertEqual(response[0]['name'], 'file.py')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/contents/path')

        asyncio.run(run_test())

    def test_get_repository_commits(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value=[{'sha': '123'}])

        async def run_test():
            response = await service.get_repository_commits('owner', 'repo')
            self.assertEqual(response[0]['sha'], '123')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/commits?per_page=30&page=1')

        asyncio.run(run_test())

    def test_get_repository_issues(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value=[{'title': 'issue'}])

        async def run_test():
            response = await service.get_repository_issues('owner', 'repo')
            self.assertEqual(response[0]['title'], 'issue')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/issues?state=open')

        asyncio.run(run_test())

    def test_get_repository_pulls(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value=[{'title': 'pull'}])

        async def run_test():
            response = await service.get_repository_pulls('owner', 'repo')
            self.assertEqual(response[0]['title'], 'pull')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/pulls?state=open')

        asyncio.run(run_test())

    def test_get_repository_contributors(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value=[{'login': 'user'}])

        async def run_test():
            response = await service.get_repository_contributors('owner', 'repo')
            self.assertEqual(response[0]['login'], 'user')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/contributors')

        asyncio.run(run_test())

    def test_get_git_tree(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value={'tree': []})

        async def run_test():
            response = await service.get_git_tree('owner', 'repo', 'sha')
            self.assertEqual(response['tree'], [])
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/git/trees/sha?recursive=1')

        asyncio.run(run_test())

    def test_get_repository_languages(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value={'Python': 100})

        async def run_test():
            response = await service.get_repository_languages('owner', 'repo')
            self.assertEqual(response['Python'], 100)
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/languages')

        asyncio.run(run_test())

    def test_get_file_content(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(return_value={'content': 'Y29udGVudA==', 'encoding': 'base64'})

        async def run_test():
            response = await service.get_file_content('owner', 'repo', 'path')
            self.assertEqual(response, 'content')
            service._make_request.assert_called_once_with('GET', '/repos/owner/repo/contents/path')

        asyncio.run(run_test())

    def test_get_file_content_not_found(self):
        service = GitHubService(github_token='test_token')
        service._make_request = AsyncMock(side_effect=GitHubResourceNotFoundError("Not Found"))

        async def run_test():
            response = await service.get_file_content('owner', 'repo', 'path')
            self.assertIsNone(response)

        asyncio.run(run_test())

    @patch('redis.Redis')
    @patch('httpx.AsyncClient')
    def test_make_request_no_content(self, mock_async_client, mock_redis):
        mock_redis.return_value.get.return_value = None
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_response.json = AsyncMock(return_value=None) # Simulate no content
        mock_response.raise_for_status = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        service = GitHubService(github_token='test_token')
        service.redis_client = mock_redis.return_value

        async def run_test():
            response = await service._make_request('GET', '/test')
            self.assertIsNone(response)
            mock_redis.return_value.setex.assert_not_called() # Should not cache if no content

        asyncio.run(run_test())
