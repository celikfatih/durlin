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

# Webhook Server (Phase 2)
WEBHOOK_PORT=8000
WEBHOOK_SECRET=your-shared-secret-configured-in-jira
WEBHOOK_VERIFY_SIGNATURE=true
TRIGGER_STATUS=Ready-for-Test

# AI
AI_API_KEY=your-openai-api-key
AI_MODEL_NAME=gpt-4o
AI_BASE_URL=https://api.openai.com/v1
AI_OUTPUT_LANGUAGE=Turkish
```

> **Note for private GitHub organizations:** After generating your token, go to [GitHub Tokens](https://github.com/settings/tokens), click **Configure SSO** next to the token, and authorize your organization.

---

## Usage

### Mode 1 — CLI (one-shot)

Run analysis for a single Jira issue and post the comment:

```bash
uv run python -m src.presentation.cli analyze PROJ-123
```

Preview the comment without posting:

```bash
uv run python -m src.presentation.cli analyze PROJ-123 --dry-run
```

Provide a specific GitHub PR URL instead of auto-discovering:

```bash
uv run python -m src.presentation.cli analyze PROJ-123 "https://github.com/org/repo/pull/42"
```

---

### Mode 2 — Webhook Server (automated)

Start Durlin as a long-running HTTP server that listens for Jira transitions:

```bash
uv run python -m src.presentation.cli serve
```

Durlin will automatically trigger the full analysis pipeline whenever a Jira issue transitions to the status defined in `TRIGGER_STATUS`.

**Webhook endpoint:** `POST /webhook/jira`
**Health check:** `GET /health`

#### Setting up the Jira Webhook

1. In Jira, go to **Settings → System → Webhooks**
2. Create a new webhook pointing to `http://your-server:8000/webhook/jira`
3. Set the JQL filter to limit events (e.g., `project = PROJ`) to reduce noise
4. Enable the **Issue Updated** event
5. Set the **Secret** to the same value as `WEBHOOK_SECRET` in your `.env`

---

## Deployment

Durlin ships with a multi-stage `Dockerfile` and `docker-compose.yml` for single-step deployment.

### Docker Compose (recommended)

```bash
docker compose up -d
```

This builds the image, starts the webhook server, and applies a health check automatically.

### Docker (manual)

```bash
docker build -t durlin .
docker run -d --env-file .env -p 8000:8000 durlin
```

### Kubernetes

Deploy the Docker image to any Kubernetes cluster. A minimal `Deployment` + `Service` manifest is all that's required — expose port `8000` and mount your `.env` variables as a `Secret` or `ConfigMap`.

### Local development with ngrok

To test webhooks locally, expose your server using [ngrok](https://ngrok.com/):

```bash
# Terminal 1 — start the server
uv run python -m src.presentation.cli serve

# Terminal 2 — create a tunnel
ngrok http 8000
```

Use the generated `https://xxxx.ngrok.io/webhook/jira` URL in your Jira Webhook configuration.

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
