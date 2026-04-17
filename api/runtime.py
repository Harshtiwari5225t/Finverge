from __future__ import annotations

import os


# Local dev runs FastAPI directly on port 8000, so we keep the `/api` prefix.
# On Vercel, the Python function itself already lives under `/api`, so routes
# should omit that prefix to avoid `/api/api/...`.
API_BASE_PREFIX = "" if os.getenv("VERCEL") else "/api"
