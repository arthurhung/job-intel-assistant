from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from job_intel.api.dependencies import get_app_settings
from job_intel.api.routers import crawlers, health, jobs, matches, resume, telegram


def create_app() -> FastAPI:
    app = FastAPI(title="Job Intel Assistant", version="0.1.0")
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(jobs.router, prefix="/api", tags=["jobs"])
    app.include_router(resume.router, prefix="/api", tags=["resume"])
    app.include_router(crawlers.router, prefix="/api", tags=["crawlers"])
    app.include_router(matches.router, prefix="/api", tags=["matches"])
    app.include_router(telegram.router, prefix="/api", tags=["telegram"])
    mount_dashboard(app)
    return app


def mount_dashboard(app: FastAPI) -> None:
    settings = get_app_settings()
    assets_dir = settings.web_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def dashboard() -> FileResponse:
        index = settings.web_dir / "index.html"
        if not index.exists():
            raise HTTPException(
                status_code=404,
                detail="Dashboard build was not found. Run `npm.cmd --prefix web run build` first.",
            )
        return FileResponse(index)


app = create_app()
