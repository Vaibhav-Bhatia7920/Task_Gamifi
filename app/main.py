from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.orm import init_db
from app.endpoints.agent import router as agent_router
from app.endpoints.auth import router as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Task Gamifi", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(agent_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
