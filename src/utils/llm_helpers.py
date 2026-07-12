"""
LLM response helper utilities.
Handles differences in response formats between providers (OpenAI, Anthropic, Google Gemini).
"""


def extract_text(response) -> str:
    """
    Extract text content from an LLM response, regardless of provider.

    Google Gemini returns response.content as a list of content parts,
    while OpenAI and Anthropic return it as a plain string.
    This function normalizes both formats to a single string.

    Args:
        response: LLM response object with a .content attribute

    Returns:
        Extracted text as a string
    """
    content = response.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        # Gemini returns list of content parts — extract text from each
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif hasattr(part, "text"):
                parts.append(part.text)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        return "\n".join(parts).strip()

    # Fallback: try converting to string
    return str(content).strip()
