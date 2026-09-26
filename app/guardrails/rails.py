import logfire
from app.utils.guardrail_response import clean_llm_response, normalize_text
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

    _rails = LLMRails(config=config, llm=guard_llm) #pass the configs to the guarded llm
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
        content_raw = result.get("content", "") if isinstance(result, dict) else str(result)


        content = clean_llm_response(content_raw)

        normalized_content = normalize_text(content)
        fired = any(
            normalize_text(indicator) in normalized_content
            for indicator in RAIL_INDICATORS
        ) #get any indicator in the content given

        logfire.info(
            "Guardrail result",
            raw_response=content_raw,
            cleaned_response=content,
            fired=fired,
        )

        if fired:
            logfire.info(
                "Guardrail fired",
                message=message,
                response=content,
            )
            return True, content

        logfire.info("Guardrails passed")
        return False, None

