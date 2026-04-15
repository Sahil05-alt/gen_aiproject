import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    vector_store_path: str = "./data/vectorstore"
    uploads_path: str = "./data/uploads"
    metadata_path: str = "./data/metadata"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://genaiproject-seven.vercel.app",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Auto-create data directories
for path in (settings.vector_store_path, settings.uploads_path, settings.metadata_path):
    Path(path).mkdir(parents=True, exist_ok=True)
