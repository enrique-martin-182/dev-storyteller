from urllib.parse import urlparse
from typing import Tuple


def extract_repo_name_from_url(url: str) -> str:
    """
    Extracts the repository name from a given URL.
    Assumes the repository name is the last part of the path,
    and removes '.git' suffix if present.
    """
    parsed_url = urlparse(url)
    # Filter out empty strings from the path components
    path_components = [component for component in parsed_url.path.split('/') if component]
    if not path_components:
        return ""
    repo_name = path_components[-1]
    return repo_name.replace('.git', '')

def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Parses a GitHub repository URL and returns the owner and repository name.
    Expected format: https://github.com/owner/repo_name(.git)
    """
    parsed_url = urlparse(url)
    
    if parsed_url.netloc != "github.com":
        raise ValueError(f"Invalid GitHub URL: Host is not github.com in {url}")

    path_components = [component for component in parsed_url.path.split('/') if component]

    if len(path_components) < 2:
        raise ValueError(f"Invalid GitHub URL format: {url}")

    owner = path_components[-2]
    repo_name = path_components[-1].replace('.git', '')
    return owner, repo_name
