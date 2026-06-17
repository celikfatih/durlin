from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class JiraIssueStatus(BaseModel):
    name: str


class JiraIssueFields(BaseModel):
    status: JiraIssueStatus


class JiraIssue(BaseModel):
    id: str
    key: str
    fields: JiraIssueFields


class ChangelogItem(BaseModel):
    field: str
    fromString: Optional[str] = None
    toString: Optional[str] = None


class Changelog(BaseModel):
    items: list[ChangelogItem] = []


class JiraWebhookPayload(BaseModel):
    webhookEvent: str
    issue: JiraIssue
    changelog: Optional[Changelog] = None
