import re

#basic utils func
def clean_llm_response(content: str) -> str:
    """Remove model reasoning blocks and return only the final response."""
    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE
    )

    return content.strip()


def normalize_text(text: str) -> str:
    return (
        text.lower()
        .replace("’", "'")
        .replace("`", "'")
        .strip()
    )