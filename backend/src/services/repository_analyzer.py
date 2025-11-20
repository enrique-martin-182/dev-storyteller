
import json

from src.services.github_service import GitHubService
from src.utils.url_utils import parse_github_url


class RepositoryAnalyzer:
    def __init__(self, github_service: GitHubService):
        self.github_service = github_service

    async def get_file_structure(self, owner: str, repo: str) -> list[dict]:
        """
        Fetches the file structure (files and directories) of a GitHub repository using the Git Trees API.
        """
        # Get the SHA of the latest commit on the default branch
        # This is a simplified approach; a more robust solution might involve getting the tree_sha directly
        # from the branch reference if available, or from the latest commit.
        # For now, we'll assume the tree_sha is directly available from the branch's latest commit.
        # A more accurate way would be to get the branch ref: /repos/{owner}/{repo}/git/ref/heads/{branch}
        # and then get the tree_sha from there.

        # For simplicity, let's get the latest commit and its tree SHA
        commits = await self.github_service.get_repository_commits(owner, repo)
        if not commits:
            return [] # No commits, no file structure

        latest_commit_sha = commits[0]["sha"]
        commit_details = await self.github_service._make_request("GET", f"/repos/{owner}/{repo}/git/commits/{latest_commit_sha}")
        tree_sha = commit_details["tree"]["sha"]

        tree_data = await self.github_service.get_git_tree(owner, repo, tree_sha)

        file_structure = []
        for item in tree_data.get("tree", []):
            file_structure.append({
                "path": item["path"],
                "type": item["type"],
                "size": item.get("size") # size is only for files
            })
        return file_structure

    async def get_commit_history(self, owner: str, repo: str, num_commits: int = 100) -> list[dict]:
        """
        Fetches the commit history for a GitHub repository with pagination and returns a simplified list.
        """
        simplified_commits = []
        page = 1
        per_page = 30  # GitHub API default per_page is 30, max 100

        while len(simplified_commits) < num_commits:
            commits_data = await self.github_service.get_repository_commits(owner, repo, per_page=per_page, page=page)
            if not commits_data:
                break # No more commits

            for commit in commits_data:
                simplified_commits.append({
                    "sha": commit["sha"],
                    "message": commit["commit"]["message"],
                    "author_name": commit["commit"]["author"]["name"],
                    "date": commit["commit"]["author"]["date"]
                })
                if len(simplified_commits) == num_commits:
                    break
            page += 1
        return simplified_commits

    async def get_repository_analysis(self, github_url: str) -> dict:
        """
        Performs a comprehensive analysis of a GitHub repository from its URL,
        including detailed language stats, commit history, file structure,
        issues, pull requests, contributors, and identified tech stack.
        """
        owner, repo_name = parse_github_url(github_url)

        # Fetch basic repository details
        repo_details = await self.github_service.get_repository_details(owner, repo_name)

        # Fetch detailed language statistics
        languages = await self.github_service.get_repository_languages(owner, repo_name)

        # Fetch issues, pull requests, and contributors
        issues = await self.github_service.get_repository_issues(owner, repo_name)
        pulls = await self.github_service.get_repository_pulls(owner, repo_name)
        contributors_data = await self.github_service.get_repository_contributors(owner, repo_name)
        contributors = [c.get("login") for c in contributors_data]

        # Fetch commit history and count total commits
        all_commits = []
        page = 1
        while True:
            commits_page = await self.github_service.get_repository_commits(owner, repo_name, page=page)
            if not commits_page:
                break
            all_commits.extend(commits_page)
            page += 1
        commit_count = len(all_commits)

        # Fetch file structure and count total files
        file_structure = await self.get_file_structure(owner, repo_name)
        file_count = len(file_structure)

        # Identify tech stack
        tech_stack = await self._identify_tech_stack(owner, repo_name)

        analysis = {
            "name": repo_details.get("name"),
            "description": repo_details.get("description"),
            "main_language": repo_details.get("language"),
            "owner": owner,
            "repo_name": repo_name,
            "languages": languages,
            "file_count": file_count,
            "commit_count": commit_count,
            "open_issues_count": len(issues),
            "open_pull_requests_count": len(pulls),
            "contributors": contributors,
            "file_structure": file_structure,
            "commit_history": all_commits, # Store full commit history for narrative generation
            "tech_stack": tech_stack,
        }
        return analysis

    async def _identify_tech_stack(self, owner: str, repo: str) -> list[str]:
        """
        Identifies the tech stack by looking for common dependency/config files.
        """
        tech_stack = set()
        common_tech_files = {
            "package.json": "Node.js/npm",
            "requirements.txt": "Python/pip",
            "pom.xml": "Java/Maven",
            "build.gradle": "Java/Gradle",
            "go.mod": "Go Modules",
            "Cargo.toml": "Rust/Cargo",
            "Gemfile": "Ruby/Bundler",
            "composer.json": "PHP/Composer",
            "Dockerfile": "Docker",
            ".nvmrc": "Node.js Version Manager",
            ".tool-versions": "asdf-vm",
            "pyproject.toml": "Python/Poetry/Flit",
            "webpack.config.js": "Webpack",
            "vite.config.js": "Vite",
            "next.config.js": "Next.js",
            "angular.json": "Angular",
            "tsconfig.json": "TypeScript",
            "tailwind.config.js": "Tailwind CSS",
            "package-lock.json": "Node.js/npm",
            "yarn.lock": "Node.js/Yarn",
            "pnpm-lock.yaml": "Node.js/pnpm",
        }

        for file_name, tech_name in common_tech_files.items():
            content = await self.github_service.get_file_content(owner, repo, file_name)
            if content:
                tech_stack.add(tech_name)
                # Further parsing for specific technologies within files can be added here
                if file_name == "package.json":
                    try:
                        package_json = json.loads(content)
                        for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                            for dep_name in package_json.get(dep_type, {}):
                                tech_stack.add(dep_name.split('/')[0]) # Add package name, remove scope if present
                    except json.JSONDecodeError:
                        pass
                elif file_name == "requirements.txt":
                    for line in content.splitlines():
                        stripped_line = line.strip()
                        if stripped_line and not stripped_line.startswith("#"):
                            tech_stack.add(stripped_line.split("==")[0].split("<")[0].split(">")[0].split("~")[0]) # Extract package name

        return sorted(tech_stack)
