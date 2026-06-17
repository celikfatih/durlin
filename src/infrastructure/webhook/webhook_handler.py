import hmac
import hashlib
import logging
from typing import Optional

from src.domain.models.webhook import JiraWebhookPayload

logger = logging.getLogger(__name__)


def verify_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """
    Verifies the X-Hub-Signature-256 header sent by Jira.

    Args:
        payload_bytes: The raw request body bytes.
        signature_header: The value of the X-Hub-Signature-256 header (e.g. 'sha256=abc...').
        secret: The shared WEBHOOK_SECRET configured in Jira and in .env.

    Returns:
        True if the signature matches, False otherwise.
    """
    expected_digest = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    expected_header = f"sha256={expected_digest}"
    return hmac.compare_digest(expected_header, signature_header)


def extract_trigger_issue_key(payload: JiraWebhookPayload, trigger_status: str) -> Optional[str]:
    """
    Inspects a Jira webhook payload and returns the issue key if the event is a
    status transition to the configured trigger status, otherwise None.

    Args:
        payload: The parsed Jira webhook payload.
        trigger_status: The Jira status name that should trigger analysis (e.g. 'Ready-for-Test').

    Returns:
        The Jira issue key string if the trigger condition is met, None otherwise.
    """
    if payload.webhookEvent != "jira:issue_updated":
        logger.debug(f"Skipping non-update event: {payload.webhookEvent}")
        return None

    if payload.changelog is None:
        logger.debug(f"No changelog in payload for issue {payload.issue.key}. Skipping.")
        return None

    for item in payload.changelog.items:
        if item.field == "status" and item.toString == trigger_status:
            logger.info(
                f"Issue {payload.issue.key} transitioned to '{trigger_status}'. Triggering analysis."
            )
            return payload.issue.key

    logger.debug(
        f"Issue {payload.issue.key} updated but no status change to '{trigger_status}'. Skipping."
    )
    return None
