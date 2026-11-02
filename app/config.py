import os
from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")
     # --- Auth (JWT) ---
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # --- Databases ---
    DATABASE_URL: str = "postgresql+asyncpg://ecom:ecom@localhost:5432/ecom"     # async (FastAPI)
    # sync_database_url: str = "postgresql+psycopg://ecom:ecom@localhost:5432/ecom" 

    # SENDER_PASSWORD:str=""
    BREVO_API_KEY : str=""
    # RESEND_API_KEY:str=""
    Sender_email:str=""
       #-----Api keys---
    GROQ_API_KEY:str=""
    COHERE_API_KEY:str=""
    OPENAI_API_KEY:str=""

    #----Qdrant----
    QDRANT_URL:str=""
    QDRANT_API_KEY:str=""
    QDRANR_collection: str = "docu_documents"
    DATA_DIR:str="data"
    UPLOAD_DIR:str="data/uploads"
    REPO_DIR:str="data/repo"
    DATABASE_URL:str

    dpi:int=150
    image_embed_dpi:int=100
    ingest_batch:int=16
    image_embed_batch:int=4
    candidate_k :int =30
    top_k:int=8
    max_context_images:int=4


    #----Models
    EMBED_MODEL:str="embed-v4.0"
    EMBED_DIM:int = 1536
    RERANK_MODEL:str = "rerank-v3.5"
    LLM_OPENAI_MODEL: str = "gpt-4o"
    LLM_GROQ_MODEL:str="qwen/qwen3.8-27b"
    LLM_GROQ_MODEL_OPENAI:str="openai/gpt-oss-120b"

    #----Auth(JWT------


def get_settings() -> Settings:
    s = Settings()

    return s