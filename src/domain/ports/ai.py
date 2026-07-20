from typing import Optional, Protocol


class AIProvider(Protocol):
    def generate_comment(
        self,
        task_title: str,
        git_diff: str,
        extra_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a structured Jira comment based on the diff.

        Args:
            task_title:   The title of the Jira task to provide context.
            git_diff:     The raw git diff content.
            extra_prompt: Optional free-text instructions appended to the user
                          message, letting callers guide the AI without editing
                          the prompt template (e.g. "Focus on migration risk.").

        Returns:
            The generated comment string, formatted as Markdown.

        Raises:
            AIGenerationError: If the AI fails to generate the content.
        """
        ...
