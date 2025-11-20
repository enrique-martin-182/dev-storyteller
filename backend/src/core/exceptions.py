class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    def __init__(self, message: str, status_code: int = None, headers: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.headers = headers or {}

class GitHubAuthError(GitHubAPIError):
    """Exception raised for GitHub authentication failures."""
    pass

class GitHubRateLimitError(GitHubAPIError):
    """Exception raised when GitHub API rate limit is exceeded."""
    def __init__(self, message: str, status_code: int, headers: dict, reset_time: int = None):
        super().__init__(message, status_code, headers)
        self.reset_time = reset_time

class GitHubResourceNotFoundError(GitHubAPIError):
    """Exception raised when a GitHub resource is not found (e.g., repository)."""
    pass
