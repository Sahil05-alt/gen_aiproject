from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    vector_store_path: str = "./data/vectorstore"
    uploads_path: str = "./data/uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Auto-create data directories
Path(settings.vector_store_path).mkdir(parents=True, exist_ok=True)
Path(settings.uploads_path).mkdir(parents=True, exist_ok=True)
