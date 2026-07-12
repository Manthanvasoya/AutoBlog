"""
SEO Agent — Generates SEO metadata for publishing platforms.
Runs in parallel with Visual agent.
Generates tags, slug, meta_description, keywords.
"""

import json
from typing import Dict, Any, List
from src.core.state import BlogState
from src.llm.prompts import get_agent_prompt
from src.llm.models import get_llm_manager
from src.utils.llm_helpers import extract_text


def seo_agent(state: BlogState) -> Dict[str, Any]:
    """
    Generate SEO metadata: tags, slug, meta_description, keywords.

    Reads: topic, outline.title, section headings
    Writes: seo_tags, meta_description, slug, keywords
    Parallel: Runs simultaneously with Visual agent
    """

    topic = state.get("topic", "")
    outline = state.get("outline", {})
    title = outline.get("title", topic)

    llm_manager = get_llm_manager()
    llm = llm_manager.get_seo_llm()

    system_prompt = get_agent_prompt("seo")

    # Get section headings for context
    section_headings = [s.get("heading", "") for s in outline.get("sections", [])]

    user_message = f"""Generate SEO metadata for this blog:

Topic: {topic}
Title: {title}
Sections: {', '.join(section_headings)}

Provide tags, meta description (150 chars max), URL slug, and keywords."""

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    # Parse JSON response
    try:
        seo_json = extract_text(response)
        if "```" in seo_json:
            seo_json = seo_json.split("```")[1].replace("json", "").strip()
        seo_data = json.loads(seo_json)
    except json.JSONDecodeError:
        # Fallback SEO data
        slug = topic.lower().replace(" ", "-")[:50]
        seo_data = {
            "tags": ["blog", topic.lower().split()[0]],
            "meta_description": f"{topic} - Learn about {topic}",
            "slug": slug,
            "keywords": [topic],
        }

    return {
        "seo_tags": seo_data.get("tags", []),
        "meta_description": seo_data.get("meta_description", ""),
        "slug": seo_data.get("slug", ""),
        "keywords": seo_data.get("keywords", []),
    }
