from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import ssl
import os

# Configuración de argumentos extra para la conexión
connect_args = {}

# Si la base es MySQL, usar SSL sin verificar certificado
# Aiven usa certificados self-signed no incluidos en el bundle del sistema
if settings.DATABASE_URL.startswith("mysql"):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    # PyMySQL acepta el objeto SSLContext directamente en la clave "ssl"
    connect_args = {"ssl": ssl_ctx}

# Crear el motor de la base de datos
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,           # Cambiar a True para ver las consultas SQL en desarrollo
    connect_args=connect_args
)

# Crear el SessionLocal para las sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
