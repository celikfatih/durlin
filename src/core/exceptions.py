class DurlinError(Exception):
    """Base exception for all Durlin errors."""
    pass

class GitDiffError(DurlinError):
    """Raised when there is an error retrieving or parsing the git diff."""
    pass

class JiraConnectionError(DurlinError):
    """Raised when Durlin cannot communicate with Jira (e.g., auth failure, network issue)."""
    pass

class AIGenerationError(DurlinError):
    """Raised when the AI provider fails to generate a valid response."""
    pass
