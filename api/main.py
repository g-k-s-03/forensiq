from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes.analyze import router as analyze_router
from api.routes.baseline import router as baseline_router
from api.routes.reports import router as reports_router

_STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI(title="ForensIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")
app.include_router(baseline_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Serve built frontend in production (when `static/` directory exists)
if _STATIC_DIR.exists():
    _assets = _STATIC_DIR / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/")
    async def root():
        return FileResponse(str(_STATIC_DIR / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(str(_STATIC_DIR / "index.html"))

else:
    @app.get("/")
    def root():
        return {"name": "ForensIQ API", "version": "1.0.0", "status": "running"}
