from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import auth, resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Resume AI - Avaliador de Currículos",
    description="API que usa IA para avaliar currículos: nota, pontos fortes/fracos, "
    "palavras-chave faltando e dicas de melhoria.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resume.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "ai_provider": settings.ai_provider}


# Serve o frontend estático (index.html) na raiz
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
