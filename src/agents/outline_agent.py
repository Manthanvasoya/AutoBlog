"""
Outline Agent — Generates detailed blog structure with sections.
Pre-filters research facts per section.
Includes HITL checkpoint for user approval.
"""

import json
from typing import Dict, Any
from langgraph.types import interrupt
from src.core.state import BlogState, OutlineSection
from src.llm.prompts import get_agent_prompt
from src.llm.models import get_llm_manager
from src.utils.llm_helpers import extract_text


def outline_agent(state: BlogState) -> Dict[str, Any]:
    """
    Generate blog outline with sections and pre-filtered facts.

    Reads: plan.outline_hints, plan.visual_requirements, summarized_facts
    Writes: outline
    HITL: Yes (embedded interrupt for user approval)
    Constraint: max_words per section hard-capped at 300
    """

    outline_hints = state["plan"].get("outline_hints", [])
    visual_requirements = state["plan"].get("visual_requirements", [])
    summarized_facts = state.get("summarized_facts", [])

    llm_manager = get_llm_manager()
    llm = llm_manager.get_outline_llm()

    system_prompt = get_agent_prompt("outline")

    # Prepare facts context
    facts_text = ""
    if summarized_facts:
        facts_text = "\n## Available Research Facts:\n"
        for fact in summarized_facts:
            facts_text += f"- {fact.get('fact', '')} (Source: {fact.get('source', '')})\n"

    # Create outline request
    user_message = f"""Create a detailed blog outline.

Outline hints: {', '.join(outline_hints)}
Visual requirements: {', '.join(visual_requirements) if visual_requirements else 'None'}

{facts_text}

Generate a logical outline with 3-7 sections. For each section:
- Assign max_words (Python will cap at 300)
- Decide if section needs a visual (and what type)
- Assign the 2-3 most relevant facts to this section"""

    # Call LLM for outline
    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    # Parse JSON response
    try:
        outline_json = extract_text(response)
        if "```" in outline_json:
            outline_json = outline_json.split("```")[1].replace("json", "").strip()
        outline = json.loads(outline_json)
    except json.JSONDecodeError:
        outline = {
            "title": "Blog Post",
            "estimated_total_words": 1500,
            "sections": [
                {
                    "heading": "Introduction",
                    "key_points": ["Overview"],
                    "needs_visual": False,
                    "visual_type": "none",
                    "relevant_facts": [],
                    "max_words": 200,
                },
                {
                    "heading": "Main Content",
                    "key_points": ["Key point"],
                    "needs_visual": False,
                    "visual_type": "none",
                    "relevant_facts": [],
                    "max_words": 1000,
                },
                {
                    "heading": "Conclusion",
                    "key_points": ["Summary"],
                    "needs_visual": False,
                    "visual_type": "none",
                    "relevant_facts": [],
                    "max_words": 200,
                },
            ],
        }

    # Python hard cap: enforce max_words <= 300 per section
    for section in outline.get("sections", []):
        section["max_words"] = min(section.get("max_words", 250), 300)

    # Recalculate estimated total
    outline["estimated_total_words"] = sum(s.get("max_words", 0) for s in outline.get("sections", []))

    # HITL Checkpoint 2: User approves or rejects the outline
    user_feedback = interrupt(
        {
            "checkpoint": "outline",
            "outline": outline,
            "message": "Review blog structure and estimated word counts",
        }
    )

    # If user provided feedback, regenerate
    if user_feedback and isinstance(user_feedback, str):
        refinement_prompt = f"""The user provided feedback on the outline: {user_feedback}

Please regenerate the outline incorporating this feedback. Output updated JSON with same fields."""

        response = llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": refinement_prompt},
            ]
        )

        try:
            outline_json = extract_text(response)
            if "```" in outline_json:
                outline_json = outline_json.split("```")[1].replace("json", "").strip()
            outline = json.loads(outline_json)

            # Reapply hard cap
            for section in outline.get("sections", []):
                section["max_words"] = min(section.get("max_words", 250), 300)
            outline["estimated_total_words"] = sum(s.get("max_words", 0) for s in outline.get("sections", []))
        except json.JSONDecodeError:
            pass

    return {"outline": outline}
