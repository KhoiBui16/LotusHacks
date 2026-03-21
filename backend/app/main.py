from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.db import close_db, init_db
from app.agent.routers.workflow import router as agent_workflow_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.claims import router as claims_router
from app.routers.me import router as me_router
from app.routers.notifications import router as notifications_router
from app.routers.settings import router as settings_router
from app.routers.uploads import router as uploads_router
from app.routers.chat import router as chat_router
from app.routers.vehicles import router as vehicles_router

app = FastAPI(
    title="LotusHacks API",
    description="Backend API for the LotusHacks website.",
    version="0.1.0",
)

default_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "https://adamnbz.github.io",
]
raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
if raw_allowed_origins:
    extra_origins = [origin.strip() for origin in raw_allowed_origins.split(",") if origin.strip()]
    allowed_origins = list(dict.fromkeys(default_allowed_origins + extra_origins))
else:
    allowed_origins = default_allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://[a-z0-9-]+\.github\.io$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(me_router)
app.include_router(vehicles_router)
app.include_router(claims_router)
app.include_router(agent_workflow_router, prefix="/api/v1/agent")
app.include_router(uploads_router)
app.include_router(notifications_router)
app.include_router(chat_router)
app.include_router(settings_router)


@app.on_event("startup")
async def on_startup():
    init_db()


@app.on_event("shutdown")
async def on_shutdown():
    close_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}
