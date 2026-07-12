"""
Writer Agent — Writes blog sections in parallel via Send API.
Each section receives only relevant facts and context (token optimization).
Supports retry with critic feedback.
"""

import json
from typing import Dict, Any, List
from langgraph.types import Send
from src.core.state import BlogState
from src.llm.prompts import format_writer_prompt
from src.llm.models import get_llm_manager
from src.utils.llm_helpers import extract_text


def writer_node(state: BlogState) -> List[Send]:
    """
    Orchestrate parallel section writing via Send API.

    Returns list of Send objects for dynamic fan-out to write_section nodes.
    """
    outline = state["outline"]
    tone = state["plan"].get("tone", "professional")
    target_audience = state["plan"].get("target_audience", "general")
    critic_feedback = state.get("critic_feedback", None)

    # Create Send for each section
    sends = []
    for i, section in enumerate(outline.get("sections", [])):
        send_input = {
            "section_index": i,
            "section": section,
            "tone": tone,
            "target_audience": target_audience,
            "critic_feedback": critic_feedback,
        }
        sends.append(Send("write_section", send_input))

    return sends


def write_section_agent(state: BlogState) -> Dict[str, Any]:
    """
    Write a single blog section (called in parallel for each section).

    Reads: section, tone, target_audience, critic_feedback (if retry)
    Writes: section content string
    """
    section = state.get("section", {})
    tone = state.get("tone", "professional")
    target_audience = state.get("target_audience", "general")
    critic_feedback = state.get("critic_feedback", None)
    section_index = state.get("section_index", 0)

    max_words = section.get("max_words", 250)
    heading = section.get("heading", "Section")
    key_points = section.get("key_points", [])
    relevant_facts = section.get("relevant_facts", [])

    llm_manager = get_llm_manager()
    llm = llm_manager.get_writer_llm()

    is_retry = critic_feedback is not None
    system_prompt = format_writer_prompt(max_words, tone, target_audience, is_retry)

    # Build user message
    user_message = f"""Write the section: {heading}

Key points to cover: {', '.join(key_points)}

Max words: {max_words}"""

    if relevant_facts:
        user_message += "\n\nRelevant research facts to incorporate:\n"
        for fact in relevant_facts:
            fact_text = fact.get("fact", "") if isinstance(fact, dict) else str(fact)
            user_message += f"- {fact_text}\n"

    if is_retry and critic_feedback:
        user_message += f"\n\nCritic feedback to address: {critic_feedback}"

    # Call LLM to write section
    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    section_content = extract_text(response)

    return {
        "sections": [section_content],  # Will be merged by collector node
        "section_index": section_index,
    }


def merge_sections(state: BlogState) -> Dict[str, Any]:
    """
    Merge all written sections into a single draft.
    Called after all parallel section writes complete.
    """
    sections = state.get("sections", [])

    # Sort sections by index and combine
    draft = "\n\n".join(sections)

    return {"draft": draft}


def writer_agent_sync(state: BlogState) -> Dict[str, Any]:
    """Synchronous version of writer agent (simulates fan-out sequentially)"""
    outline = state["outline"]
    tone = state["plan"].get("tone", "professional")
    target_audience = state["plan"].get("target_audience", "general")
    critic_feedback = state.get("critic_feedback", None)

    sections = []
    for i, section in enumerate(outline.get("sections", [])):
        send_input = {
            "section_index": i,
            "section": section,
            "tone": tone,
            "target_audience": target_audience,
            "critic_feedback": critic_feedback,
        }
        result = write_section_agent(send_input)
        sections.extend(result["sections"])

    draft = "\n\n".join(sections)
    return {"sections": sections, "draft": draft}
