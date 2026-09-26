import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI
#we are using chatopenai to hit the port key

from app.config import settings

# we need the config for the gateway
#   - fallback: primary @ragbot/openai/gpt-oss-120b; 2ndary @ragbot1/openai/gpt-oss-120b (Different accounts)
#   -cache: semantic mode (requires portkey)
#   -retry: 2 attempts on rate limit
GATEWAY_CONFIG = {
    "strategy": {"mode": "fallback"},
    "cache": {"mode" : "simple"},
    "retry":{
        "attempts" : 2,
        "on_status_codes": [429, 503]
    },
    "targets": [
        {"override_params": {"model" : f"@{settings.GROQ_SLUG_1}/{settings.GROQ_MODEL}"}},
        {"override_params": {"model" : f"@{settings.GROQ_SLUG_2}/{settings.GROQ_FALLBACK_MODEL}"}}
    ]
}

portkey_client = Portkey(
    api_key=settings.PORTKEY_API_KEY,
    config=GATEWAY_CONFIG,
)

def get_langchain_llm(feature: str = "ragbot") -> ChatOpenAI:

    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
    )