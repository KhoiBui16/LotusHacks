from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import close_db, init_db
from app.routers.auth import router as auth_router

app = FastAPI(
    title="LotusHacks API",
    description="Backend API for the LotusHacks website.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
async def on_startup():
    init_db()


@app.on_event("shutdown")
async def on_shutdown():
    close_db()


@app.get("/health")
async def health_check():
    return {"status": "ok"}
