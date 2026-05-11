from fastapi import FastAPI

from app.api import fitting, outfit
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="Fit-Mate-LLM", version="0.1.0")
app.include_router(outfit.router)
app.include_router(fitting.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
