from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Configuración de base de datos
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:1234@localhost:3306/siniestros_scisp"
    )
    
    # Configuración de autenticación
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "tu_clave_secreta_muy_segura_aqui_cambiala"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Configuración de la aplicación
    PROJECT_NAME: str = "API Conteos SCISP"
    PROJECT_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()
