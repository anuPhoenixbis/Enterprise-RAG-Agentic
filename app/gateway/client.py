import logfire
from portkey_ai import Portkey, createHeaders, PORTKEY_GATEWAY_URL
from langchain_openai import ChatOpenAI
#we are using chatopenai to hit the port key

from app.config import settings

# we need the config for the gateway
#   - fallback: primary @ragbot/openai/gpt-oss-120b; 2ndary @ragbot1/openai/gpt-oss-120b (Different accounts)
#   -cache: semantic mode (requires portkey)
#   -retry: 2 attempts on rate limit
# GATEWAY_CONFIG = {
#     "strategy": {"mode": "fallback"},
#     "cache": {"mode" : "simple"},
#     "retry":{
#         "attempts" : 2,
#         "on_status_codes": [429, 503]
#     },
#     "targets": [
#         {"override_params": {"model" : f"@{settings.GROQ_SLUG_1}/{settings.GROQ_MODEL}"}},
#         {"override_params": {"model" : f"@{settings.GROQ_SLUG_2}/{settings.GROQ_FALLBACK_MODEL}"}}
#     ]
# }
#
# portkey_client = Portkey(
#     api_key=settings.PORTKEY_API_KEY,
#     config=GATEWAY_CONFIG,
# )

def get_langchain_llm(feature: str = "ragbot") -> ChatOpenAI:
    model = (
        f"@{settings.GROQ_SLUG_2}/{settings.GROQ_MODEL_CLASSIFICATION}"
        if feature == "planner"
        else f"@{settings.GROQ_SLUG_1}/{settings.GROQ_MODEL}"
    )

    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        #when planner feature is invoked then use the other slug with classification mode
        # otherwise use the normal model
        model=model,
        temperature=0,
        default_headers=createHeaders(
            api_key=settings.PORTKEY_API_KEY,
            config=settings.PORTKEY_CONFIG,
            metadata={
                "feature": feature,
                "_user": "rag-bot",
                "environment": "dev"
            }
        )
    )

def extract_cache_status(response) -> str:
    # cache the query itself for the next time
    for attr in ("_raw_response","_response","_http_response"):
        raw = getattr(response, attr, None)
        if raw is not None:
            status = getattr(raw, "headers", {}).get("x-portkey-cache-status", "")
            if status:
                return status.upper() #cache hit
    return "MISS" #cache miss