from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers.tasks import router as task_router
from app.routers.auth import router as auth_router
from app.routers.submissions import router as submissions_router
from app.routers.reviews import router as reviews_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="SimpleBackend",
    description="学习激励与协作平台接口",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(task_router)
app.include_router(auth_router)
app.include_router(submissions_router)
app.include_router(reviews_router)

@app.get("/")
def root():
    return {"message": "Backend is active"}

@app.get("/health")
def health():
    return {"status": "ok"}

