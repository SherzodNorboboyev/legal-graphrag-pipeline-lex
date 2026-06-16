"""Application configuration and logging setup.

This module centralizes all runtime configuration for the Legal GraphRAG
pipeline for lex. Values are loaded from environment variables and, during local
development, from a `.env` file.

No secrets should be hardcoded in source code. Use `.env` locally and a proper
secret manager in production.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Literal

from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Typed application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_env: str = Field(default="local", alias="APP_ENV", description="Application environment (e.g., 'development', 'production').")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR').")

    # -------------------------------------------------------------------------
    # Data directories
    # -------------------------------------------------------------------------
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR", description="Base directory for data storage.")
    raw_dir: Path = Field(default=Path("data/raw"), alias="RAW_DIR", description="Base directory for raw data storage.")
    markdown_dir: Path = Field(default=Path("data/markdown"), alias="MARKDOWN_DIR", description="Base directory for markdown data storage.")
    sample_output_dir: Path = Field(default=Path("data/sample_output"), alias="SAMPLE_OUTPUT_DIR", description="Base directory for sample output data storage.")
    crawl_checkpoint_file: Path = Field(default=Path("data/crawl_checkpoint.json"), alias="CRAWL_CHECKPOINT_FILE", description="File for storing crawl checkpoint data.")
    embedding_cache_path: Path = Field(default=Path("data/embedding_cache.sqlite3"), alias="EMBEDDING_CACHE_PATH", description="DB for caching embeddings.")

    # -------------------------------------------------------------------------
    # Source websites
    # -------------------------------------------------------------------------
    source_url: str = Field(default="https://lex.uz/", alias="SOURCE_URL", description="URL of the source website to crawl.")
    scrape_english: bool = Field(default=False, alias="SCRAPE_ENGLISH", description="Whether to scrape English content from the source website.")
    scrape_uzbek: bool = Field(default=True, alias="SCRAPE_UZBEK", description="Whether to scrape Uzbek content from the source website.")
    scrape_russian: bool = Field(default=False, alias="SCRAPE_RUSSIAN", description="Whether to scrape Russian content from the source website.")

    # -------------------------------------------------------------------------
    # Scraper behavior
    # -------------------------------------------------------------------------
    use_playwright: bool = Field(default=True, alias="USE_PLAYWRIGHT", description="Whether to use Playwright for scraping dynamic content.")
    max_pages: int = Field(default=100, alias="MAX_PAGES", description="Maximum number of pages to crawl.")
    request_timeout_seconds: int = Field(default=30, alias="REQUEST_TIMEOUT_SECONDS", description="Timeout for HTTP requests in seconds.")
    request_retries: int = Field(default=3, alias="REQUEST_RETRIES", description="Number of retries for failed HTTP requests.")
    throttle_min_seconds: float = Field(default=1.0, alias="THROTTLE_MIN_SECONDS", description="Minimum number of seconds to wait between requests.")
    throttle_max_seconds: float = Field(default=3.5, alias="THROTTLE_MAX_SECONDS", description="Maximum number of seconds to wait between requests.")

    # -------------------------------------------------------------------------
    # Neo4j
    # -------------------------------------------------------------------------
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI", description="URI for the Neo4j database.")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME", description="Username for the Neo4j database.")
    neo4j_password: str = Field(default="neo4j-password", alias="NEO4J_PASSWORD", description="Password for the Neo4j database.")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE", description="Database name for the Neo4j database.")
    neo4j_vector_dimension: int = Field(default=1536, gt=0, alias="NEO4J_VEXTOR_DIMENSION", description="Dimension of the vector index in Neo4j.")

    # -------------------------------------------------------------------------
    # Embeddings
    # -------------------------------------------------------------------------
    embedding_provider: Literal["sentence_transformers", "openai"] = Field(default="sentence_transformers", alias="EMBEDDING_PROVIDER", description="Provider for generating embeddings.")
    sentence_transformers_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="SENTENCE_TRANSFORMERS_MODEL", description="Model for sentence transformers.")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL", description="Model for OpenAI embeddings.")
    openai_api_key: str = Field(default="your-openai-api-key", alias="OPENAI_API_KEY", description="API key for OpenAI embeddings.")
    openai_embedding_dimension: int = Field(default=1024, gt=0, alias="OPENAI_EMBEDDING_DIMENSION", description="Dimension of the OpenAI embeddings.")

    # -------------------------------------------------------------------------
    # LLM topic extraction and answer synthesis
    # -------------------------------------------------------------------------
    topic_llm_provider: Literal["fallback", "openai"] = Field(default="fallback", alias="TOPIC_LLM_PROVIDER", description="Provider for LLM topic extraction.")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL", description="Model for OpenAI chat.")
    topic_extraction_max_retries: int = Field(default=3, ge=0, alias="TOPIC_EXTRACTION_MAX_RETRIES", description="Maximum number of retries for topic extraction.")
    synthesis_provider: Literal["fallback", "openai"] = Field(default="fallback", alias="SYNTHESIS_PROVIDER", description="Provider for answer synthesis.")

    # -------------------------------------------------------------------------
    # Chunking
    # -------------------------------------------------------------------------
    CHUNK_MIN_TOKENS: int = Field(default=500, ge=50, alias="CHUNK_MIN_TOKENS", description="Minimum number of tokens in a chunk.")
    CHUNK_MAX_TOKENS: int = Field(default=900, ge=100, alias="CHUNK_MAX_TOKENS", description="Maximum number of tokens in a chunk.")
    CHUNK_OVERLAP_TOKENS: int = Field(default=120, ge=0, alias="CHUNK_OVERLAP_TOKENS", description="Number of overlapping tokens between chunks.")

    # -------------------------------------------------------------------------
    # Hybrid retrieval
    # -------------------------------------------------------------------------
    HYBRID_VECTOR_WEIGHT: float = Field(default=0.65, ge=0, le=1, alias="HYBRID_VECTOR_WEIGHT", description="Weight for the vector component in hybrid retrieval.")
    HYBRID_KEYWORD_WEIGHT: float = Field(default=0.35, ge=0, le=1, alias="HYBRID_KEYWORD_WEIGHT", description="Weight for the keyword component in hybrid retrieval.")
    RERANKING_ENABLED: bool = Field(default=False, alias="RERANKING_ENABLED", description="Whether to enable reranking in hybrid retrieval.")
    CROSS_ENCODER_MODEL: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="CROSS_ENCODER_MODEL", description="Model for cross-encoding in hybrid retrieval.")

    # -------------------------------------------------------------------------
    # Topic merging
    # -------------------------------------------------------------------------
    topic_merge_similarity_threshold: float = Field(default=0.88, ge=0, le=1, alias="TOPIC_MERGE_SIMILARITY_THRESHOLD", description="Similarity threshold for merging topics.")

    @field_validator("source_url")
    @classmethod
    def ensure_trailing_slash(cls, value: str, info: Any) -> str:
        """Ensure that URL fields have a trailing slash."""

        value = value.strip()
        return value if value.endswith("/") else f"{value}/"
    
    @field_validator("throttle_min_seconds", "throttle_max_seconds")
    @classmethod
    def ensure_positive_duration(cls, value: int, info: Any) -> int:
        """Ensure that throttle seconds is a positive integer."""

        if value < 0:
            raise ValueError("Throttle seconds must be a positive integer.")
        return value
    
    @field_validator("throttle_max_seconds")
    @classmethod
    def validate_throttle_range(cls, value: int, info: Any) -> int:
        """Ensure that throttle_max_seconds is greater than or equal to throttle_min_seconds."""

        min_seconds = info.data.get("throttle_min_seconds", 0.0)
        if value < min_seconds:
            raise ValueError("THROTTLE_MAX_SECONDS must be greater than or equal to THROTTLE_MIN_SECONDS.")
        return value
    
    @field_validator("chunk_max_tokens")
    @classmethod
    def ensure_positive_chunk_max_tokens(cls, value: int, info: Any) -> int:
        """Ensure that chunk_max_tokens is a positive integer."""

        if value <= 0:
            raise ValueError("CHUNK_MAX_TOKENS must be a positive integer.")
        return value
    
    @field_validator("chunk_max_tokens")
    @classmethod
    def validate_chunk_range(cls, value: int, info: Any) -> int:
        """Ensure that CHUNK_MAX_TOKENS is greater than CHUNK_MIN_TOKENS."""

        min_tokens = info.data.get("chunk_min_tokens", 500)
        if value < min_tokens:
            raise ValueError("CHUNK_MAX_TOKENS must be greater than or equal to CHUNK_MIN_TOKENS.")
        return value
    
    @field_validator("chunk_overlap_tokens")
    @classmethod
    def validate_chunk_overlap(cls, value: int, info: Any) -> int:
        """Ensure that CHUNK_OVERLAP_TOKENS is less than CHUNK_MAX_TOKENS."""

        max_tokens = info.data.get("chunk_max_tokens", 900)
        if value >= max_tokens:
            raise ValueError("CHUNK_OVERLAP_TOKENS must be less than CHUNK_MAX_TOKENS.")
        return value
    
    @property
    def active_embedding_dimensions(self) -> int:
        """Return the dimension of the active embedding model based on the provider."""
        
        if self.embedding_provider == "openai":
            return self.openai_embedding_dimension
        return self.neo4j_vector_dimensions
    
    @property
    def is_openai_available(self) -> bool:
        """Check if OpenAI API key is set and provider is selected."""

        return self.embedding_provider == "openai" and bool(self.openai_api_key and self.openai_api_key.strip())
    
    def ensure_directories(self) -> None:
        """Ensure that all necessary directories exist, creating them if needed."""

        directories = [
            self.data_dir,
            self.raw_dir,
            self.markdown_dir,
            self.sample_output_dir,
            self.checkpoint_file.parent,
            self.embedding_cache_path.parent,
        ]

        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
          
def configure_logging(level: str | None = None) -> None:
    """Configure Loguru logging for CLI commands.

    Parameters
    ----------
    level:
        Optional explicit logging level. If not provided, `LOG_LEVEL` from the
        environment is used, falling back to `INFO`.
    """

    log_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()

    logger.remove()  # Remove default logger
    logger.add(
        sys.stderr, 
        level=log_level, 
        backtrace=False,
        diagnose=False,
        enqueue=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
    )

@lru_cache(max_size=1)
def get_settings() -> Settings:
    """Load, validate, cache, and return application settings."""

    settings = Settings()
    settings.ensure_directories()
    return settings

def log_startup_summary(settings: Settings) -> None:
    """Log a concise startup summary without exposing secrets."""

    logger.info("Application environment: {}", settings.app_env)
    logger.info("Data directory: {}", settings.data_dir)
    logger.info("Raw directory: {}", settings.raw_dir)
    logger.info("Markdown directory: {}", settings.markdown_dir)
    logger.info("Source URL: {}", settings.source_url)
    logger.info("Neo4j URI: {}", settings.neo4j_uri)
    logger.info("Neo4j database: {}", settings.neo4j_database)
    logger.info("Embedding provider: {}", settings.embedding_provider)
    logger.info("Embedding dimensions: {}", settings.active_embedding_dimensions)
    logger.info("OpenAI configured: {}", settings.is_openai_available)