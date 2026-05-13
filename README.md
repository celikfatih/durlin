<div align="center">

# Durlin

**AI-powered CLI that turns Jira issues into detailed technical comments — automatically.**

Durlin connects to Jira, discovers linked GitHub Pull Requests, fetches their diffs, and uses an AI model to generate a structured, multi-section technical summary that is posted directly back to your Jira issue.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## How It Works

```
Jira Issue Key
      │
      ▼
Jira Dev Status API ──► Linked GitHub PRs & Commits
      │
      ▼
GitHub REST API ──► Raw .diff content
      │
      ▼
AI Model ──► Structured technical comment (via prompt-template.md)
      │
      ▼
Jira Comment Posted
```

No local Git clone required. Durlin fetches everything remotely.

---

## Features

- **Auto-discovery** — Resolves Jira issues to linked GitHub PRs and commits via the Jira Dev Status API
- **Remote diff fetching** — Reads diffs directly from the GitHub API; works with private repositories
- **Configurable output language** — Set any language via `AI_OUTPUT_LANGUAGE` in your `.env`
- **Customizable prompt** — AI behavior is driven by `prompt-template.md`, a plain text file you can edit without touching code
- **Dry-run mode** — Preview the generated comment in your terminal without posting to Jira
- **OpenAI-compatible** — Works with any OpenAI-compatible endpoint (Azure OpenAI, NVIDIA NIM, etc.)

---

## Requirements

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) package manager
- A Jira Cloud account with an [API token](https://id.atlassian.com/manage-profile/security/api-tokens)
- A GitHub [Personal Access Token](https://github.com/settings/tokens) with `repo` scope
- An OpenAI API key (or compatible endpoint)

---

## Installation

```bash
git clone https://github.com/your-org/durlin.git
cd durlin
uv sync
```

---

## Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

```env
# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=you@example.com
JIRA_API_TOKEN=your-jira-api-token

# GitHub
GITHUB_TOKEN=your-github-personal-access-token

# AI
AI_API_KEY=your-openai-api-key
AI_MODEL_NAME=gpt-4o
AI_BASE_URL=https://api.openai.com/v1
AI_OUTPUT_LANGUAGE=Turkish
```

> **Note for private GitHub organizations:** After generating your token, go to [GitHub Tokens](https://github.com/settings/tokens), click **Configure SSO** next to the token, and authorize your organization. Otherwise, requests to private repositories will return `404`.

---

## Usage

### Auto-discover from Jira (recommended)

```bash
uv run python -m src.presentation.cli PROJ-123
```

Durlin fetches the Jira issue, discovers all linked GitHub PRs and commits, retrieves their diffs, generates the comment, and posts it.

### Preview without posting

```bash
uv run python -m src.presentation.cli PROJ-123 --dry-run
```

### Provide a specific GitHub URL

```bash
uv run python -m src.presentation.cli PROJ-123 "https://github.com/org/repo/pull/42"
```

---

## Customizing the Output

All AI behavior is controlled by `src/infrastructure/ai/prompt_template.md`. Edit this file to change:

- Section structure and order
- Formatting rules
- Tone and verbosity

The template uses a `{{LANGUAGE}}` placeholder which Durlin replaces at runtime with the value of `AI_OUTPUT_LANGUAGE` from your `.env`. This means **all section headings, labels, and fallback messages** will be produced in the configured language — not just the body content.

To switch the output to English:

```env
AI_OUTPUT_LANGUAGE=English
```

Changes take effect immediately on the next run — no code changes needed.

---

## Generated Comment Structure

| Section | Description |
|---|---|
| Change Type | Feature / Bug fix / Refactor / Performance / Mixed with justification |
| Technical Summary | Modified classes, methods, endpoints, and business logic |
| Behavioral Impact | Runtime behavior changes, new execution paths, error handling |
| API & Integration Impact | Breaking changes, endpoint signatures, external service changes |
| Data Layer Impact | Database schema, query, and persistence changes |
| QA Recommendations | Actionable test scenarios derived strictly from the diff |
| Risk Analysis | Low / Medium / High with technical justification |
| Overall Assessment | Deployment considerations and areas requiring careful review |

---

## License

MIT — see [LICENSE](LICENSE) for details.
