from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyze import router as analyze_router
from api.routes.baseline import router as baseline_router
from api.routes.reports import router as reports_router

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


@app.get("/")
def root():
    return {"name": "ForensIQ API", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
