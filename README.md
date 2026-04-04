# Adajoon - TV & Radio from Around the World

A containerized application that connects to online TV station databases, discovers channels, categorizes them, and provides powerful search functionality.

## Features

- **Channel Discovery** — Automatically fetches and indexes thousands of live TV channels from the [iptv-org](https://github.com/iptv-org/iptv) public database
- **Category Browsing** — Channels organized by category (News, Sports, Entertainment, Music, etc.)
- **Country Filtering** — Filter channels by country of origin (200+ countries)
- **Full-Text Search** — Search by channel name, network, or alternate names
- **Built-in Video Player** — Watch live streams directly in the browser (HLS support)
- **Auto-Sync** — Channel data refreshes automatically from upstream sources
- **Responsive UI** — Works on desktop and mobile

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend   │────▶│  PostgreSQL  │
│  React/Vite  │     │   FastAPI   │     │   Database   │
│  nginx:80    │     │  uvicorn    │     │   port 5432  │
│  port 3000   │     │  port 8000  │     │              │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  iptv-org   │
                    │  Public API │
                    └─────────────┘
```

## Quick Start

```bash
docker compose up --build
```

Then open [http://localhost:3000](http://localhost:3000).

The backend will automatically sync channel data on startup (takes ~30-60 seconds). You can also trigger a manual sync:

```bash
curl -X POST http://localhost:8000/api/sync
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/channels` | List/search channels (supports `query`, `category`, `country`, `language`, `page`, `per_page`) |
| GET | `/api/channels/{id}` | Get channel details |
| GET | `/api/channels/{id}/streams` | Get available streams for a channel |
| GET | `/api/categories` | List all categories with channel counts |
| GET | `/api/countries` | List all countries with channel counts |
| GET | `/api/stats` | Get database statistics |
| POST | `/api/sync` | Trigger manual data sync |
| GET | `/api/health` | Health check |

## Development

### Backend only

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend**: React 18, Vite, HLS.js
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Data Source**: [iptv-org/api](https://github.com/iptv-org/api)

---

## Using Skills

This project includes comprehensive coding skills to ensure consistency and quality. Skills work across different AI assistant contexts.

### 🤖 Cursor Agent Mode (Automatic)

When using Cursor's Agent mode (full-screen AI assistant), skills are **automatically loaded** from `.cursor/skills/` and applied based on context:

- Working on backend code? → `adajoon-backend`, `adajoon-security`, `adajoon-database` skills apply
- Creating React components? → `adajoon-frontend`, `adajoon-security` skills apply
- Writing migrations? → `adajoon-database` skill applies
- Deploying? → `adajoon-deployment` skill applies

**No action needed** - just start working, and Agent will reference the appropriate skills.

### 💬 Cursor Composer/Chat Mode

For Cursor's Composer (Cmd+I) or Chat (Cmd+L) modes:

1. **Quick rules**: Cursor automatically reads `.cursorrules` at the project root
   - Provides concise guidelines for common patterns
   - Applies to all code changes

2. **Detailed reference**: Use @-mentions for comprehensive guidance
   ```
   @.cursor/skills/CLAUDE.md review my authentication code
   ```

3. **Specific skills**: Reference individual skill files
   ```
   @.cursor/skills/adajoon-backend/SKILL.md how should I structure this API endpoint?
   ```

### 🧠 Direct Claude Conversations (Outside Cursor)

When using Claude directly (web, API, or other editors):

1. **Copy the reference file**: Open `.cursor/skills/CLAUDE.md`
2. **Find relevant section**: Use search (Cmd/Ctrl+F) for your topic
3. **Paste into conversation**: Include the relevant section in your prompt

**Example**:
```
I'm working on authentication in Adajoon. Here are the security patterns:

[Paste Security section from CLAUDE.md]

Please review my code against these patterns...
```

### 📚 Available Skills

**7 specialized skills** covering all aspects of the codebase:

1. **adajoon-backend** (407 lines) - FastAPI patterns, authentication, CSRF, caching
2. **adajoon-frontend** (400 lines) - React hooks, API calls, OAuth integration
3. **adajoon-security** (531 lines) - Security headers, JWT, CSRF, input validation
4. **adajoon-database** (404 lines) - SQLAlchemy models, Alembic migrations
5. **adajoon-deployment** (450 lines) - Railway, Docker, environment config
6. **adajoon-conventions** (435 lines) - Code quality, naming, comments
7. **adajoon-skill-improvement** (940 lines) - Continuous improvement process

**Total**: ~2,867 lines of comprehensive guidelines

### 🔍 Quick Pattern Lookup

**Common questions → Where to look**:

| Question | File | Section |
|----------|------|---------|
| How do I add CSRF protection? | `.cursorrules` or `CLAUDE.md` | Backend > CSRF Protection |
| What's the cookie security pattern? | `.cursorrules` or `CLAUDE.md` | Security > Cookie Security |
| How do I create a migration? | `.cursorrules` or `CLAUDE.md` | Database > Migration Template |
| What's the React hook pattern? | `.cursorrules` or `CLAUDE.md` | Frontend > Custom Hooks |
| How do I structure API endpoints? | `.cursorrules` or `CLAUDE.md` | Backend > Router Structure |
| How do I deploy to Railway? | `.cursorrules` or `CLAUDE.md` | Deployment > Railway Architecture |

### 📝 Updating Skills

Skills evolve with the codebase. When you discover a bug or pattern violation:

1. **Fix the issue** in your code
2. **Update the skill** to prevent recurrence
3. **Document the learning** (see `adajoon-skill-improvement` skill)

Skills are versioned and include changelogs. See `.cursor/skills/adajoon-skill-improvement/SKILL.md` for the full process.

### 🎯 Single Source of Truth

All three skill formats (Cursor Agent, `.cursorrules`, `CLAUDE.md`) reference the **same underlying content** in `.cursor/skills/`. Changes to one skill file automatically benefit all contexts.

---
