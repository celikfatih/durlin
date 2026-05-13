import requests
from src.domain.ports.git import GitProvider
from src.core.exceptions import GitDiffError

class GitHubHTTPProvider(GitProvider):
    def __init__(self, github_token: str = ""):
        self.github_token = github_token

    def get_diff(self, url: str) -> str:
        if not url:
            raise GitDiffError("URL cannot be empty.")
            
        # Clean up URL if it has .diff at the end
        clean_url = url[:-5] if url.endswith(".diff") else url
        
        # Convert github.com web URLs to api.github.com REST URLs
        api_url = clean_url
        if "github.com/" in clean_url:
            parts = clean_url.split("github.com/")[-1].split("/")
            if len(parts) >= 4:
                owner = parts[0]
                repo = parts[1]
                entity_type = parts[2]
                entity_id = parts[3]
                
                if entity_type == "pull":
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{entity_id}"
                elif entity_type == "commit":
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{entity_id}"
        
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
            
        try:
            response = requests.get(api_url, headers=headers, timeout=15)
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
