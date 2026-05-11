import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import conteos, auth, catalogo
from app.core.database import engine
from app.models import models
import logging

# Crear las tablas durante el evento de startup. En producción la BD puede no estar
# disponible en el momento del arranque (por ejemplo, provisión en Railway). En
# lugar de fallar el proceso, capturamos errores y dejamos que el servidor arranque
# para que el healthcheck pueda responder y los logs muestren el problema.
logger = logging.getLogger("uvicorn.error")


@app.on_event("startup")
async def on_startup_create_tables():
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        # No abortar el arranque: la plataforma (Railway) podrá mostrar logs y permitir
        # que el servicio responda al healthcheck para diagnóstico.
        logger.exception("Failed to create database tables on startup: %s", e)

app = FastAPI(
    title="API Conteos SCISP",
    description="API para el sistema de conteos de productos en sucursales",
    version="1.0.0"
)

# Orígenes permitidos: variable de entorno ALLOWED_ORIGINS (separados por coma)
# o wildcard "*" si no está definida (útil en desarrollo)
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if _allowed_origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in _allowed_origins_env.split(",")]

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
