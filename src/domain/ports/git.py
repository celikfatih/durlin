from typing import Protocol

class GitProvider(Protocol):
    def get_diff(self, url: str) -> str:
        """
        Fetch the git diff for a given pull request or commit URL.
        
        Args:
            url: The GitHub URL (e.g., 'https://github.com/org/repo/pull/123')
            
        Returns:
            The raw diff output as a string.
            
        Raises:
            GitDiffError: If the diff cannot be retrieved.
        """
        ...
