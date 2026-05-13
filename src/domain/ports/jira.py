from typing import Protocol

class JiraProvider(Protocol):
    def get_issue_title(self, issue_key: str) -> str:
        """
        Fetch the title/summary of a Jira task.
        
        Args:
            issue_key: The Jira issue identifier (e.g., 'PROJ-123')
            
        Returns:
            The title/summary of the issue.
            
        Raises:
            JiraConnectionError: If the issue cannot be retrieved.
        """
        ...
        
    def get_issue(self, issue_key: str) -> dict:
        """
        Fetch the full issue dictionary including its numeric ID.
        """
        ...
        
    def get_development_links(self, issue_id: str) -> dict:
        """
        Fetch the development data (commits, PRs) for the given internal issue ID.
        """
        ...
        
    def add_comment(self, issue_key: str, comment: str) -> None:
        """
        Post a comment to a Jira issue.
        
        Args:
            issue_key: The Jira issue identifier (e.g., 'PROJ-123')
            comment: The text to post as a comment.
            
        Raises:
            JiraConnectionError: If the comment cannot be posted.
        """
        ...
