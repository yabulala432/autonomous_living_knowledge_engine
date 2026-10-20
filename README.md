# Autonomous Living Knowledge Engine (ShadowOps AI)

> **An event-driven AI system that monitors engineering discussions and code changes, continuously detects documentation drift, and automatically drafts sync pull requests and executive sprint digests.**

---

## 📖 Overview

Most engineering teams struggle with **documentation drift**: wikis, READMEs, and architecture docs become outdated because developers make decisions in Slack threads and GitHub PRs without updating the documentation.

The **Autonomous Living Knowledge Engine** solves this by operating silently in the background:
* **Detects Documentation Drift**: Analyzes incoming GitHub PRs and Slack messages for architectural decisions, searches existing documentation with semantic similarity, and flags contradictions.
* **Automated Fix PRs**: Generates proposed diffs and opens sync pull requests against the documentation repository.
* **Decision Archaeology**: Indexes the context and rationale behind architectural decisions for fast semantic retrieval.
* **Sprint Synthesis**: Automatically compiles decisions, changes, and events into client- or executive-ready progress reports.

---

## 🏗️ Architecture & Pipeline

```text
[ Sources: GitHub PRs / Slack Events ]
                 │
                 ▼
     [ FastAPI Webhook Gateway ]
                 │
                 ▼
  [ 1. LLM Decision Extractor ] ───> Checks if event is an architectural decision
                 │
                 ▼
  [ 2. OpenAI Embedding Engine ] ───> text-embedding-3-small
                 │
                 ▼
  [ 3. PostgreSQL + pgvector ] ─────> Semantic similarity search against stored docs
                 │
                 ▼
  [ 4. Drift Evaluator Agent ] ─────> Identifies contradictions & generates diffs
                 │
                 ▼
  [ 5. Automated Action Dispatcher ]
    ├── 🚨 Drift Detected: Opens automated doc-fix Pull Request
    └── 📊 Sprint Reports: Compiles multi-day summaries via /reports/sprint
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* Python 3.10+
* PostgreSQL 16+ with the [`pgvector`](https://github.com/pgvector/pgvector) extension installed.
* An OpenAI API Key (`text-embedding-3-small` and `gpt-4o`/`gpt-4o-mini`).

### 2. Environment Setup
Create a `.env` file in the project root:

```env
# Your OpenAI API Key for embeddings and decision extraction
OPENAI_API_KEY="sk-proj-..."

# PostgreSQL connection string with pgvector enabled
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/shadowops"

# (Optional) GitHub Personal Access Token for opening real PRs
GITHUB_TOKEN="ghp_..."

# (Optional) Telegram Bot credentials for notifications and event ingestion
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
TELEGRAM_CHAT_ID="-1001234567890"
```

### 3. Database Initialization
Ensure PostgreSQL has the `vector` extension enabled, then apply the database schema:

```bash
# Enable vector and initialize tables
psql "postgresql://postgres:postgres@localhost:5432/shadowops" -f app/database/schema.sql
```

*(If running on Windows with PostgreSQL 18, install `pgvector` binaries via `scripts/install_pgvector.ps1` as Administrator, or run PostgreSQL with `pgvector/pgvector:pg17` via Docker).*

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Start the Application Server
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## 🔗 Connecting Your Data Sources

To connect your real GitHub repositories and Slack workspaces to the system:

### A. Connecting GitHub Repositories

1. **Expose your local server to the Internet**:
   Since webhooks require a publicly accessible URL, use [ngrok](https://ngrok.com/) during local development:
   ```bash
   ngrok http 8000
   ```
   Note the forwarding URL (e.g. `https://xyz123.ngrok-free.app`).

2. **Configure the GitHub Webhook**:
   * Open your GitHub repository and go to **Settings** -> **Webhooks** -> **Add webhook**.
   * **Payload URL**: `https://<your-ngrok-url>/webhooks/github`
   * **Content type**: `application/json`
   * **Events**: Select **Let me select individual events**, then check:
     * `Pull requests`
     * (Optional) `Pushes`
   * Click **Add webhook**.

### B. Connecting Slack

1. Go to the [Slack API App Console](https://api.slack.com/apps) and click **Create New App**.
2. Navigate to **Event Subscriptions**:
   * Toggle **Enable Events** to **On**.
   * **Request URL**: `https://<your-ngrok-url>/webhooks/slack`
   * Under **Subscribe to bot events**, add `message.channels`.
3. Install the app to your workspace.
4. Invite the bot to your engineering channels:
   ```text
   /invite @YourBotName
   ```

### C. Connecting Telegram

Telegram can be used both to **ingest engineering decisions** discussed in group chats and to **receive real-time drift alerts & sprint reports**.

1. **Create a Bot with BotFather**:
   * Open Telegram and search for [`@BotFather`](https://t.me/BotFather).
   * Send `/newbot`, choose a name and username, and copy the **Bot API Token**.
   * Add it to your `.env` as `TELEGRAM_BOT_TOKEN="<your-token>"`.

2. **Get your Group/Channel Chat ID**:
   * Add your bot to your engineering group or channel.
   * Send a test message in the group.
   * Open `https://api.telegram.org/bot<your-token>/getUpdates` in your browser.
   * Look for `"chat": {"id": -100xxxxxxxxxx, ...}` and set `TELEGRAM_CHAT_ID="-100xxxxxxxxxx"` in `.env`.

3. **Set the Telegram Webhook (to ingest messages)**:
   Register your public ngrok URL with the Telegram Bot API:
   ```bash
   curl -F "url=https://<your-ngrok-url>/webhooks/telegram" "https://api.telegram.org/bot<your-token>/setWebhook"
   ```
   Now, any discussion in the group is streamed to `/webhooks/telegram` for decision extraction. When drift is detected, the bot automatically sends an alert directly to your Telegram chat.

### D. Registering Your Repository Documentation

The engine checks incoming decisions against existing documentation stored in the `documents` table.

You can index your repository docs using the seed pattern found in `scripts/seed_data.py`:

```python
from app.services.embeddings import generate_embedding

# Read your repo markdown doc (e.g., docs/architecture/auth.md)
with open("docs/architecture/auth.md", "r", encoding="utf-8") as f:
    doc_content = f.read()

# Generate semantic embedding
embedding = await generate_embedding(doc_content)

# Store document in database
await conn.execute(
    """
    INSERT INTO documents (workspace_id, repo_name, file_path, content, last_commit_hash, embedding)
    VALUES ($1, $2, $3, $4, $5, $6)
    """,
    workspace_id,
    "your-org/your-repo",
    "docs/architecture/auth.md",
    doc_content,
    "git-commit-hash",
    embedding
)
```

---

## 🧪 Testing the End-to-End Flow

### 1. Seed Sample Document
Populate the database with a mock architecture document (`docs/architecture/auth.md` specifying a Redis session TTL of 24 hours):
```bash
python scripts/seed_data.py
```

### 2. Simulate a Conflicting GitHub PR
Send a simulated PR merge changing the TTL from 24 hours to 1 hour:
```bash
curl -X POST http://127.0.0.1:8000/webhooks/github \
     -H "Content-Type: application/json" \
     -d '{
       "sender": {"login": "dev1"},
       "pull_request": {
         "url": "https://github.com/org/repo/pull/1",
         "body": "Security update: we are reducing the Redis session TTL from 24 hours to 1 hour to comply with new standards."
       }
     }'
```

Watch your server terminal output. You will see:
1. The decision extracted via LLM.
2. Embedding generated and indexed.
3. Candidate documents retrieved via vector similarity.
4. `🚨 DRIFT DETECTED in docs/architecture/auth.md` flagged.
5. Simulated Pull Request generated with updated content.

### 3. Generate a Sprint Digest
Generate a summary report of all decisions over the last 7 days:
```bash
curl -X GET "http://127.0.0.1:8000/reports/sprint?days=7"
```

---

## 📂 Project Structure

```text
├── app/
│   ├── core/
│   │   └── config.py          # Settings and environment variables
│   ├── database/
│   │   ├── connection.py      # AsyncPG connection pool & pgvector registration
│   │   └── schema.sql         # Database schema (workspaces, events, decisions, docs, drift_tickets)
│   ├── models/
│   │   └── schemas.py         # Pydantic schemas for extraction & drift results
│   ├── services/
│   │   ├── embeddings.py      # OpenAI embedding generation
│   │   ├── evaluator.py       # LLM drift evaluation and diff drafting
│   │   ├── extractor.py       # LLM decision extraction from raw payloads
│   │   ├── github.py          # Action dispatcher / PR generation
│   │   ├── retrieval.py       # pgvector cosine similarity retrieval
│   │   └── synthesis.py       # Sprint digest synthesizer
│   └── main.py                # FastAPI routes & background task pipeline
├── scripts/
│   ├── install_pgvector.ps1   # Windows PostgreSQL 18 pgvector installer
│   └── seed_data.py           # Seeds sample documents with embeddings
├── setup.md                   # Setup guide
└── README.md                  # Project overview & documentation
```

---

## 🛠️ API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/webhooks/github` | `POST` | Ingests GitHub pull requests and commit events |
| `/webhooks/slack` | `POST` | Ingests Slack message and reaction events |
| `/webhooks/telegram` | `POST` | Ingests Telegram group discussions and messages |
| `/reports/sprint` | `GET` | Compiles recent decisions and events into a summary (`?days=7`) |
| `/reports/sprint/telegram` | `POST` | Compiles and pushes the sprint digest directly to Telegram (`?days=7`) |
| `/health` | `GET` | Application health check |
