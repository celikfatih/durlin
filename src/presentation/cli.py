import typer
import logging
from rich.console import Console
from rich.panel import Panel
from src.core.config import get_settings
from src.core.exceptions import DurlinError
from src.infrastructure.git.github_http import GitHubHTTPProvider
from src.infrastructure.jira.api_client import JiraAPIClient
from src.infrastructure.ai.openai_client import OpenAIProvider
from src.domain.services.analyzer import DiffAnalyzerService

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = typer.Typer(
    name="Durlin", 
    help="AI-Powered Jira Comment Generator from Git Diffs",
    add_completion=False
)
console = Console()

import typing

@app.command()
def analyze(
    issue_key: str = typer.Argument(..., help="The Jira Issue Key (e.g., PROJ-123)"),
    git_ref: typing.Optional[str] = typer.Argument(None, help="Optional Git reference for the diff (e.g., 'master...branch'). If omitted, Durlin discovers commits from Jira directly."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate the comment but do not post it to Jira")
):
    """
    Generate a technical Jira comment from a git diff and optionally post it to Jira.
    """
    try:
        # Load configuration
        settings = get_settings()
        
        # Initialize providers (Dependency Injection)
        git_provider = GitHubHTTPProvider(github_token=settings.GITHUB_TOKEN)
        jira_provider = JiraAPIClient(
            server_url=settings.JIRA_URL,
            user_email=settings.JIRA_USER_EMAIL,
            api_token=settings.JIRA_API_TOKEN
        )
        
        # Using OpenAI implementation as decided
        ai_provider = OpenAIProvider(
            base_url=settings.AI_BASE_URL,
            api_key=settings.AI_API_KEY,
            model_name=settings.AI_MODEL_NAME,
            language=settings.AI_OUTPUT_LANGUAGE
        )
        
        # Initialize Orchestrator
        analyzer = DiffAnalyzerService(
            git_provider=git_provider,
            jira_provider=jira_provider,
            ai_provider=ai_provider
        )
        
        # Execute
        console.print(f"[bold blue]Starting Durlin Analysis for {issue_key}...[/bold blue]")
        generated_comment = analyzer.analyze_and_comment(
            issue_key=issue_key, 
            git_reference=git_ref, 
            dry_run=dry_run
        )
        
        # Display Result
        console.print(Panel(generated_comment, title="Generated Jira Comment", expand=False, border_style="green"))
        
        if dry_run:
            console.print("[yellow]Note: Comment was NOT posted to Jira (--dry-run)[/yellow]")
        else:
            console.print(f"[bold green]Successfully posted comment to Jira: {issue_key}[/bold green]")
            
    except DurlinError as e:
        console.print(f"[bold red]Durlin Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {str(e)}")
        raise typer.Exit(code=2)

if __name__ == "__main__":
    app()
