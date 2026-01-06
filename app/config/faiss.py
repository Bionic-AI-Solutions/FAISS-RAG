"""
FAISS (vector search) configuration using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FAISSSettings(BaseSettings):
    """FAISS configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="FAISS_",
    )

    # FAISS Index Configuration
    index_path: str = Field(default="/data/faiss_indices", description="FAISS index storage path")
    index_type: str = Field(default="IndexFlatL2", description="FAISS index type")
    dimension: int = Field(default=768, description="Vector dimension")
    use_mmap: bool = Field(default=True, description="Use memory-mapped files for persistence")


# Global FAISS settings instance
faiss_settings = FAISSSettings()








