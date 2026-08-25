import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import movistar
from app.services.bot_commands import register_bot_commands
from app.services.change_detection import bootstrap_signatures, poll_catalogue_changes

logger = logging.getLogger("movistar-parati")
settings = get_settings()


async def _poll_loop() -> None:
    while True:
        try:
            await poll_catalogue_changes()
        except Exception:
            logger.exception("Poll failed")
        await asyncio.sleep(settings.poll_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_signatures()
    await register_bot_commands()
    task = asyncio.create_task(_poll_loop())
    logger.info("Movistar Para Ti started (NocoDB CMS, poll=%ss)", settings.poll_interval_seconds)
    yield
    task.cancel()


app = FastAPI(title="Movistar Para Ti", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(movistar.router)

STATIC = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "nocodb": bool(settings.nocodb_products_table_id)}


@app.get("/movistar-demo/admin")
@app.get("/movistar-demo/admin/")
def admin_page():
    return FileResponse(STATIC / "admin" / "index.html")
