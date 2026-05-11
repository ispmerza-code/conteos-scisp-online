import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import conteos, auth, catalogo
from app.core.database import engine
from app.models import models

logger = logging.getLogger("uvicorn.error")

# app debe definirse ANTES de cualquier decorador @app.*
app = FastAPI(
    title="API Conteos SCISP",
    description="API para el sistema de conteos de productos en sucursales",
    version="1.0.0"
)


@app.on_event("startup")
async def on_startup_create_tables():
    """Crea las tablas al arrancar; captura errores para no bloquear el healthcheck."""
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.exception("Failed to create database tables on startup: %s", e)

# Orígenes permitidos: variable de entorno ALLOWED_ORIGINS (separados por coma)
# Nota: allow_credentials=True es incompatible con allow_origins=["*"] (estándar CORS)
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if _allowed_origins_env == "*":
    allowed_origins = ["*"]
    allow_credentials = False
else:
    allowed_origins = [o.strip() for o in _allowed_origins_env.split(",")]
    allow_credentials = True

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(conteos.router, prefix="/api/v1/conteos", tags=["Conteos"])
app.include_router(catalogo.router)


@app.get("/")
async def root():
    return {"message": "API Conteos SCISP - Sistema de conteos de productos"}


@app.get("/health")
async def health():
    # Endpoint ligero para healthchecks externos (debe responder muy rápido)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
