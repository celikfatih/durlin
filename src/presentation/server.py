import logging
from typing import Optional

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import ValidationError

from src.core.config import Settings, get_settings
from src.domain.models.webhook import JiraWebhookPayload
from src.domain.services.analyzer import DiffAnalyzerService
from src.infrastructure.git.github_http import GitHubHTTPProvider
from src.infrastructure.jira.api_client import JiraAPIClient
from src.infrastructure.ai.openai_client import OpenAIProvider
from src.infrastructure.webhook.webhook_handler import verify_signature, extract_trigger_issue_key

logger = logging.getLogger(__name__)


def _build_analyzer(settings: Settings) -> DiffAnalyzerService:
    """Construct the DiffAnalyzerService with all providers wired up."""
    return DiffAnalyzerService(
        git_provider=GitHubHTTPProvider(github_token=settings.GITHUB_TOKEN),
        jira_provider=JiraAPIClient(
            server_url=settings.JIRA_URL,
            user_email=settings.JIRA_USER_EMAIL,
            api_token=settings.JIRA_API_TOKEN,
        ),
        ai_provider=OpenAIProvider(
            base_url=settings.AI_BASE_URL,
            api_key=settings.AI_API_KEY,
            model_name=settings.AI_MODEL_NAME,
            language=settings.AI_OUTPUT_LANGUAGE,
        ),
    )


def _run_analysis(issue_key: str, settings: Settings) -> None:
    """Background task: run the full analysis pipeline for a single issue."""
    try:
        analyzer = _build_analyzer(settings)
        analyzer.analyze_and_comment(issue_key=issue_key, dry_run=False)
        logger.info(f"[{issue_key}] Analysis complete — comment posted to Jira.")
    except Exception as e:
        logger.error(f"[{issue_key}] Analysis failed: {e}", exc_info=True)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Factory function that creates and returns the configured FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Durlin Webhook Server",
        description="Listens for Jira issue transitions and auto-generates technical comments.",
        version="2.0.0",
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/webhook/jira", status_code=200)
    async def jira_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> dict:
        raw_body = await request.body()

        # --- Signature Verification (optional, controlled by config) ---
        if settings.WEBHOOK_VERIFY_SIGNATURE:
            if not settings.WEBHOOK_SECRET:
                logger.error("WEBHOOK_VERIFY_SIGNATURE is True but WEBHOOK_SECRET is not set.")
                raise HTTPException(status_code=500, detail="Server misconfiguration: missing webhook secret.")

            signature_header = request.headers.get("X-Hub-Signature-256", "")
            if not signature_header:
                raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256 header.")

            if not verify_signature(raw_body, signature_header, settings.WEBHOOK_SECRET):
                logger.warning("Rejected webhook: invalid signature.")
                raise HTTPException(status_code=403, detail="Invalid webhook signature.")

        # --- Parse Payload ---
        try:
            payload = JiraWebhookPayload.model_validate_json(raw_body)
        except ValidationError as e:
            logger.warning(f"Received unparseable webhook payload: {e}")
            return {"status": "ignored", "reason": "unparseable payload"}

        # --- Check Trigger Condition ---
        issue_key = extract_trigger_issue_key(payload, settings.TRIGGER_STATUS)
        if issue_key is None:
            return {"status": "ignored", "reason": "trigger condition not met"}

        # --- Dispatch Analysis as Background Task ---
        # We return 200 immediately so Jira doesn't time out waiting for AI processing.
        logger.info(f"[{issue_key}] Trigger matched '{settings.TRIGGER_STATUS}'. Dispatching analysis.")
        background_tasks.add_task(_run_analysis, issue_key, settings)

        return {"status": "accepted", "issue": issue_key}

    return app
