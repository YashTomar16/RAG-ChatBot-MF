# Frontend (Vercel)

React + TypeScript + Vite app for the HDFC Mutual Fund Assistant.

## Setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `VITE_API_URL` to your Railway backend URL (e.g. `https://your-api.up.railway.app`).

Local dev uses the Vite proxy — requests to `/api/*` forward to `http://localhost:8000`.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server at http://localhost:5173 |
| `npm run build` | Production build → `dist/` |
| `npm run preview` | Preview production build |

## Deploy to Vercel

1. Import the repo and set **Root Directory** to `frontend`.
2. Add environment variable: `VITE_API_URL=https://your-railway-api.up.railway.app`
3. Deploy — `vercel.json` handles SPA routing.

## Backend (Railway)

From the repo root:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Set on Railway: `GROQ_API_KEY`, `CORS_ORIGINS=https://your-app.vercel.app`, plus embedding vars from `.env.example`.

Ensure the vector index is built on Railway (`python -m src.ingest.indexer`) or baked into the deploy artifact.
