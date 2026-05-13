from typing import Protocol

class AIProvider(Protocol):
    def generate_comment(self, task_title: str, git_diff: str) -> str:
        """
        Generate a structured Jira comment in Turkish based on the diff.
        
        Args:
            task_title: The title of the Jira task to provide context.
            git_diff: The raw git diff content.
            
        Returns:
            The generated comment string, formatted appropriately.
            
        Raises:
            AIGenerationError: If the AI fails to generate the content.
        """
        ...
