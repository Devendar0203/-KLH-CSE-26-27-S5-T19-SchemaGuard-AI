import os

class Settings:
    PROJECT_NAME: str = "SchemaGuard AI"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./schemaguard.db")

settings = Settings()
