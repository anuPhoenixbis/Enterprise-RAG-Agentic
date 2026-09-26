import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS

_rails: LLMRails | None = None

def initialize_rails() -> None:
    # build nemo LLMRails singleton at app startup
    #for chat classification : openai/gpt-oss-20b
    #for rag : openai/gpt-oss-120b

    global _rails

    guard_llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL_CLASSIFICATION,
        temperature=0 #no creativity needed
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT,
    )

    _rails = LLMRails(config, llm=guard_llm) #pass the configs to the guarded llm
    logfire.info("Nemo Guardrails initialized: openai/gpt-oss-20b")

def guard(message: str) -> tuple[bool, str | None]:
    #run a user msg thru guardrails gate
    #returns:
    #   (True, rail_response) -> rail fired; return the response instantly, skip rag pipeline
    #   (False, None) -> msg is clean, proceed to langgraph

    if _rails is None:
        logfire.warning("Guardrails not initialized - skipping gate")
        return False, None

    with logfire.span("Guardrails check"):
        result = _rails.generate(messages=[{"role": "user", "content": message}])

        #nemo results
        content = result.get("content", "") if isinstance(result, dict) else str(result)

        fired = any(indicator in content for indicator in RAIL_INDICATORS) #get any indicator in the content given

        if fired:
            logfire.info(f"Guardrails fired | query={message[:80]}")
            return True, content

        logfire.info("Guardrails passed")
        return False, None