import requests
from src.domain.ports.git import GitProvider
from src.core.exceptions import GitDiffError


class GitHubHTTPProvider(GitProvider):
    def __init__(self, github_token: str = ""):
        self.github_token = github_token

    def _make_headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers

    def _fetch(self, api_url: str) -> str:
        """Performs the HTTP GET and returns the raw diff text."""
        try:
            response = requests.get(api_url, headers=self._make_headers(), timeout=30)
            response.raise_for_status()
            diff_text = response.text
            if not diff_text.strip():
                raise GitDiffError(f"GitHub returned an empty diff for URL: {api_url}")
            return diff_text
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "Unknown"
            text = e.response.text if e.response is not None else str(e)
            raise GitDiffError(f"HTTP error fetching diff from GitHub: {status} - {text}") from e
        except requests.exceptions.RequestException as e:
            raise GitDiffError(f"Network error fetching diff from GitHub: {str(e)}") from e

    def _parse_github_url(self, url: str) -> tuple[str, str, str, list[str]]:
        """
        Parse a github.com URL and return (owner, repo, entity_type, rest_parts).
        Raises GitDiffError if the URL cannot be parsed as a GitHub URL.
        """
        if "github.com/" not in url:
            raise GitDiffError(f"Not a recognised GitHub URL: {url}")
        parts = url.split("github.com/")[-1].rstrip("/").split("/")
        if len(parts) < 3:
            raise GitDiffError(f"GitHub URL too short to parse: {url}")
        owner, repo, entity_type = parts[0], parts[1], parts[2]
        rest = parts[3:]
        return owner, repo, entity_type, rest

    def get_diff(self, url: str) -> str:
        """
        Fetch the diff for a GitHub PR, single commit, or compare URL.

        Supported URL forms:
          - PR:      https://github.com/org/repo/pull/123
          - Commit:  https://github.com/org/repo/commit/<sha>
          - Compare: https://github.com/org/repo/compare/master...abc1234
        """
        if not url:
            raise GitDiffError("URL cannot be empty.")

        clean_url = url[:-5] if url.endswith(".diff") else url

        owner, repo, entity_type, rest = self._parse_github_url(clean_url)

        if entity_type == "pull" and rest:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{rest[0]}"
        elif entity_type == "commit" and rest:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{rest[0]}"
        elif entity_type == "compare" and rest:
            # e.g. compare/master...abc1234  —  rest[0] is 'master...abc1234'
            api_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{rest[0]}"
        else:
            raise GitDiffError(
                f"Unrecognised GitHub URL structure: {url}. "
                "Expected /pull/<n>, /commit/<sha>, or /compare/<base>...<head>."
            )

        return self._fetch(api_url)

    def get_compare_diff(self, repo_url: str, base: str, head: str) -> str:
        """
        Fetch the cumulative diff between two refs (branches, tags, or commit SHAs)
        using the GitHub Compare API.

        Args:
            repo_url: Any GitHub URL that identifies the repository
                      (e.g. 'https://github.com/org/repo' or a PR/commit URL from that repo).
            base:     The base ref to compare from (e.g. 'master', 'main', a commit SHA).
            head:     The head ref / commit SHA to compare to.

        Returns:
            The raw unified diff as a string.
        """
        if not repo_url:
            raise GitDiffError("repo_url cannot be empty.")

        owner, repo, *_ = self._parse_github_url(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
        return self._fetch(api_url)
