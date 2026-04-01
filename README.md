# ReTV - Online TV Channel Browser

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
