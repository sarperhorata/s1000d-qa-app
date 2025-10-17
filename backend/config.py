"""
Configuration module for S1000D QA application
Handles environment-based configuration for local and Azure deployments
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # CORS
    CORS_ORIGINS_STR = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:3004,http://127.0.0.1:3000"
    )
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]
    
    # PDF Path
    PDF_PATH = os.getenv(
        "PDF_PATH",
        "/Users/sarperhorata/s1000d QA/S1000D Issue 6/Specification/S1000D Issue 6.PDF"
    )
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chromadb")  # chromadb or faiss
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "s1000d_docs")
    
    # Embedding Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2
    
    # Chunking Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # OCR Configuration
    OCR_ENABLED = os.getenv("OCR_ENABLED", "true").lower() == "true"
    OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")  # tesseract or easyocr
    OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "eng").split(",")
    
    # Processing Configuration
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    
    @classmethod
    def is_local(cls) -> bool:
        """Check if running in local environment"""
        return cls.ENVIRONMENT == "local"
    
    @classmethod
    def is_azure(cls) -> bool:
        """Check if running in Azure environment"""
        return cls.ENVIRONMENT == "azure"


class AzureConfig(Config):
    """Azure-specific configuration"""
    
    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER", "s1000d-docs")
    AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
    
    # Azure Key Vault
    AZURE_KEYVAULT_URL = os.getenv("AZURE_KEYVAULT_URL", "")
    
    # Azure Container Apps
    AZURE_CONTAINER_REGISTRY = os.getenv("AZURE_CONTAINER_REGISTRY", "")
    AZURE_RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "")
    AZURE_CONTAINER_APP_NAME = os.getenv("AZURE_CONTAINER_APP_NAME", "s1000d-qa-app")
    
    # Azure Computer Vision (optional upgrade)
    AZURE_COMPUTER_VISION_ENDPOINT = os.getenv("AZURE_COMPUTER_VISION_ENDPOINT", "")
    AZURE_COMPUTER_VISION_KEY = os.getenv("AZURE_COMPUTER_VISION_KEY", "")
    
    @classmethod
    def validate_azure_config(cls) -> tuple[bool, list[str]]:
        """Validate Azure configuration"""
        errors = []
        
        if not cls.AZURE_STORAGE_CONNECTION_STRING:
            errors.append("AZURE_STORAGE_CONNECTION_STRING not set")
        
        if not cls.AZURE_BLOB_CONTAINER:
            errors.append("AZURE_BLOB_CONTAINER not set")
        
        return len(errors) == 0, errors


def get_config() -> Config:
    """Get appropriate configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "local")
    
    if env == "azure":
        return AzureConfig()
    
    return Config()


# Global config instance
config = get_config()

