import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_COLLECTION = "enterprise_rag"

    GROQ_MODEL = "openai/gpt-oss-120b"
    GROQ_MODEL_CLASSIFICATION = "openai/gpt-oss-20b"
    GROQ_FALLBACK_MODEL = "qwen/qwen3.8-27b"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")

    #groq slugs
    GROQ_SLUG_1 = os.getenv("GROQ_SLUG_1")
    GROQ_SLUG_2 = os.getenv("GROQ_SLUG_2")

settings = Settings()