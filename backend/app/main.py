from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.accounting.routes import router as accounting_router
from app.config import APP_CONFIG
from app.invoices.routes import router as invoice_router

app = FastAPI(title="Invoice Review")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(APP_CONFIG.allowed_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(invoice_router)
app.include_router(accounting_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if APP_CONFIG.static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=APP_CONFIG.static_dir / "assets"), name="assets")

    @app.get("/")
    @app.get("/{requested_path:path}")
    def frontend(requested_path: str = "") -> FileResponse:
        """Serve the built React app without intercepting API routes registered above."""
        candidate = (APP_CONFIG.static_dir / requested_path).resolve()
        static_root = APP_CONFIG.static_dir.resolve()
        if candidate.is_relative_to(static_root) and candidate.is_file():
            return FileResponse(candidate)

        index = APP_CONFIG.static_dir / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Frontend build is not available.")
        return FileResponse(index)
