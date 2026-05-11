from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Configuración de argumentos extra para la conexión
connect_args = {}

# Si la base es MySQL (mysql+pymysql://...), activamos SSL
if settings.DATABASE_URL.startswith("mysql"):
    azure_ca_bundle = "/etc/ssl/certs/ca-certificates.crt"
    if os.path.exists(azure_ca_bundle):
        connect_args = {
            "ssl": {
                # Bundle de certificados del contenedor (Azure App Service Linux)
                "ca": azure_ca_bundle
            }
        }

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
