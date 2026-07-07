"""
RENDER-KA reference implementation — FastAPI health/ready/ping routes.
Drop into src/routes/ of any NahaLabs FastAPI service.

Rules:
- /health and /ping: no DB, no Redis, no LLM, no model loading. Must stay <100ms.
- /ready: the ONLY place allowed to check real dependencies.
"""

import os
import time
from fastapi import APIRouter

router = APIRouter()

APP_NAME = os.getenv("APP_NAME", "unnamed-service")
APP_VERSION = os.getenv("APP_VERSION", "0.0.0")


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@router.get("/ping")
async def ping():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    """
    Checks real dependencies. Extend with your actual clients
    (Supabase/Postgres, Redis, vector store, Ollama) but keep each
    check fast and fail gracefully — this endpoint answers
    'can I serve real traffic right now', not '/health'.
    """
    checks = {}
    overall_ok = True

    # Example pattern — replace with real client calls:
    # try:
    #     await db.execute("SELECT 1")
    #     checks["database"] = "ok"
    # except Exception as e:
    #     checks["database"] = f"error: {e}"
    #     overall_ok = False

    checks["service"] = APP_NAME
    checks["checked_at"] = time.time()

    return {
        "status": "ready" if overall_ok else "degraded",
        "checks": checks,
    }
