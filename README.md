# Render Keep-Alive Hub

Central GitHub Actions hub that pings Render Free Tier services on a schedule so
they don't spin down and cold-start on the next real request.

This repo implements the **RENDER-KA** standard (see
[`RENDER_KEEPALIVE_STANDARD.md`](./RENDER_KEEPALIVE_STANDARD.md)). One hub pings
every NahaLabs Render service — no per-project workflow needed.

## How it works

- A single GitHub Actions workflow (`.github/workflows/keep-alive.yml`) runs
  every **10 minutes** via cron (and on manual `workflow_dispatch`).
- It reads target URLs from [`urls.txt`](./urls.txt), one per line.
- For each URL it issues an HTTP GET with a 15s timeout and logs
  `timestamp, endpoint, status_code, latency_ms, success/failure`.
- Individual failures never fail the workflow — the hub's only job is to keep
  pinging on schedule, not to gate CI.
- Optional: set the `NOTIFY_WEBHOOK` repo secret (Slack/Discord webhook) to get
  a notification when any endpoint fails.

## Repository structure

```
render-keepalive/
├── RENDER_KEEPALIVE_STANDARD.md   # The RENDER-KA standard (read this first)
├── README.md
├── urls.txt                        # One target URL per line
├── .github/
│   └── workflows/
│       └── keep-alive.yml          # Cron pinger, every 10 min
└── src/
    └── routes/
        └── health.py               # Reference FastAPI health/ready/ping routes
```

## Add a new service

1. Make sure the service exposes a `/health` or `/ping` endpoint (see the
   standard and `src/routes/health.py` for the contract).
2. Add a line to `urls.txt`:

   ```
   https://your-service.onrender.com/ping
   ```

3. Done. The next scheduled run picks it up automatically — no workflow edits.

Lines starting with `#` are treated as comments and skipped.

## Health endpoint contract (per the standard)

| Endpoint | Purpose | May touch DB/LLM? |
|---|---|---|
| `GET /health` | Cheap liveness + service/version | No |
| `GET /ping` | Instant 200, for keep-alive pingers only | No |
| `GET /ready` | Real dependency checks (DB, Redis, models) | Yes |

`/health` and `/ping` must never call OpenAI, Anthropic, Gemini, Ollama,
embeddings, OCR, or any inference pipeline. Keep them under 100ms.

## Local reference routes

`src/routes/health.py` is a drop-in FastAPI `APIRouter` implementing all three
endpoints. Copy it into any NahaLabs FastAPI service under `src/routes/` and
include the router in your app.

## Environment variables (per service)

| Variable | Purpose |
|---|---|
| `APP_NAME` | Service identifier in logs/health payload |
| `APP_VERSION` | Version string in `/health` |
| `RENDER_EXTERNAL_URL` | Render-provided public URL |
| `PORT` | Bind port (Render sets this) |

## Manual actions after setup

- In the repo **Settings → Actions → General**, ensure Actions are allowed and
  the workflow has permission to run on schedule.
- (Optional) Add a `NOTIFY_WEBHOOK` secret for failure alerts.
- Uncomment the URLs in `urls.txt` once each service is live and exposes
  `/ping`.

## Honest limit

Nothing here can force Render to never sleep — that's Render's platform policy.
This hub reduces cold starts to near-zero by keeping traffic flowing; it does
not override Render's resource management. See the standard for the recommended
layered-defense combo for revenue-critical services.
