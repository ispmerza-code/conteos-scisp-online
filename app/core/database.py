from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import ssl
import os

# Configuración de argumentos extra para la conexión
connect_args = {}

# Si la base es MySQL, configurar SSL con el certificado CA de Aiven
if settings.DATABASE_URL.startswith("mysql"):
    # Ruta al CA cert de Aiven incluido en el repositorio
    ca_cert_path = os.path.join(os.path.dirname(__file__), "..", "..", "ca.pem")
    ca_cert_path = os.path.abspath(ca_cert_path)

    ssl_ctx = ssl.create_default_context(cafile=ca_cert_path if os.path.exists(ca_cert_path) else None)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED if os.path.exists(ca_cert_path) else ssl.CERT_NONE
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
