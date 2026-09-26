from app.agents.state import AgentState
from app.gateway.client import extract_cache_status, get_langchain_llm
import logfire

#direct groq call -> llm gateway (portkey routing//fallback/calls)
# llm = ChatGroq(
#     api_key=settings.GROQ_API_KEY,
#     model = settings.GROQ_MODEL,
# )
#using the portkey client

llm = get_langchain_llm()

def generate_node(state: AgentState):
    #synthesis a response using both docs context and convo history
    query = state["current_query"]
    history_str = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    user_msg = state["messages"][-1]["content"] if state["messages"] else ""

    if query == "CONVERSATIONAL":
        logfire.info("Generating conversational response using memory")
        prompt = f"""
                You are a friendly and helpful Enterprise AI Assistant.
                Answer the user's latest message using the CONVERSATION HISTORY below.

                CONVERSATION HISTORY:
                {history_str}

                LATEST MESSAGE:
                "{user_msg}"
                """
    else:
        logfire.info("Generating technical RAG response")
        max_context_chars = 25000
        full_context = ""

        for doc in state["documents"]:
            # get each of the docs provided by the user
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning("Context truncated to fit Groq TPM limits")
                break

        prompt = f"""
                You are a Senior Technical Architect.
                Answer the question using the TECHNICAL CONTEXT provided.

                TECHNICAL CONTEXT:
                {full_context}

                CONVERSATION HISTORY:
                {history_str}

                USER QUESTION:
                "{user_msg}"
                """

    with logfire.span("LLM synthesis"):
        try:

            # using the portkey here
            response = llm.invoke(prompt)

            # content = llm.invoke(prompt).content

            content = response.content
            cache_status = extract_cache_status(content)
            is_cache_hit = cache_status == "HIT"

            if is_cache_hit:
                logfire.info("Gateway Cache hit -> response served by portkey")
                plan_update = state["plan"] + ["Cache: Hit"]
                status = "Cache hit - instant response"
            else:
                logfire.info("Response generated via LLM")
                plan_update = state["plan"]
                status = "Response generated"

            return {
                "final_answer": content,
                "status": status,
                "plan": plan_update,
                "messages": [{"role": "assistant", "content": content}],
            }
        except Exception as e:
            logfire.error(f"LLM Generation failed: {e}")
            raise e
