import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routes import admin, api, telegram
from app.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("movistar-parati")

settings = get_settings()
app = FastAPI(title="Movistar Para ti API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(admin.router)
app.include_router(telegram.router)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    logger.info("Movistar Para ti API started (demo_mode=%s)", settings.demo_mode)


@app.get("/health")
def health():
    return {"status": "ok", "demo": settings.demo_mode}


@app.get("/app")
@app.get("/app/")
def miniapp():
    return FileResponse(STATIC_DIR / "miniapp" / "index.html")


@app.get("/panel")
@app.get("/panel/")
def admin_panel():
    return FileResponse(STATIC_DIR / "admin" / "index.html")
