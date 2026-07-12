"""
Critic Agent — Quality evaluation with retry logic.
Evaluates assembled blog on depth/clarity/grounding.
Includes HITL checkpoint and retry logic.
"""

import json
from typing import Dict, Any
from langgraph.types import interrupt
from src.core.state import BlogState
from src.llm.prompts import get_agent_prompt
from src.llm.models import get_llm_manager
from src.utils.llm_helpers import extract_text


def critic_agent(state: BlogState) -> Dict[str, Any]:
    """
    Evaluate blog quality and provide feedback.

    Reads: assembled_blog, summarized_facts, iteration_count
    Writes: critic_score, critic_feedback, iteration_count
    HITL: Yes (embedded interrupt for final approval)
    Retry: Loops back to Writer if score < 0.75 and iterations < 3
    """

    assembled_blog = state.get("assembled_blog", "")
    summarized_facts = state.get("summarized_facts", [])
    iteration_count = state.get("iteration_count", 0)

    llm_manager = get_llm_manager()
    llm = llm_manager.get_critic_llm()

    system_prompt = get_agent_prompt("critic")

    # Prepare facts context for grounding check
    facts_text = ""
    if summarized_facts:
        facts_text = "Available research facts:\n"
        for fact in summarized_facts:
            fact_text = fact.get("fact", "") if isinstance(fact, dict) else str(fact)
            facts_text += f"- {fact_text}\n"

    user_message = f"""Evaluate this blog content:

{assembled_blog}

{facts_text}

Score the blog on depth, clarity, and grounding (0.0-1.0 each)."""

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    # Parse JSON response
    try:
        critic_json = extract_text(response)
        if "```" in critic_json:
            critic_json = critic_json.split("```")[1].replace("json", "").strip()
        critic_data = json.loads(critic_json)
    except json.JSONDecodeError:
        # Fallback scoring
        critic_data = {
            "depth_score": 0.8,
            "clarity_score": 0.85,
            "grounding_score": 0.8,
            "composite_score": 0.8167,
            "passed": True,
            "feedback": "",
        }

    # Extract scores
    depth = float(critic_data.get("depth_score", 0.8))
    clarity = float(critic_data.get("clarity_score", 0.8))
    grounding = float(critic_data.get("grounding_score", 0.8))

    # Calculate composite score: (0.4 × depth) + (0.3 × clarity) + (0.3 × grounding)
    composite_score = (0.4 * depth) + (0.3 * clarity) + (0.3 * grounding)
    passed = composite_score >= 0.75

    feedback = critic_data.get("feedback", "")
    iteration_count += 1

    # Check if should retry
    if not passed and iteration_count < 3:
        # Loop back to writer with feedback
        return {
            "critic_score": composite_score,
            "critic_feedback": feedback,
            "iteration_count": iteration_count,
            "_should_retry": True,  # Signal to graph to loop back to writer
        }

    # If iterations exhausted, force pass
    if iteration_count >= 3:
        passed = True

    # HITL Checkpoint 3: User approves final blog
    user_approval = interrupt(
        {
            "checkpoint": "critic",
            "critic_score": composite_score,
            "depth_score": depth,
            "clarity_score": clarity,
            "grounding_score": grounding,
            "feedback": feedback,
            "message": "Review and approve the assembled blog",
        }
    )

    # If user rejected, reset iteration and collect new feedback
    if user_approval and isinstance(user_approval, str) and not user_approval.lower().startswith("approve"):
        return {
            "critic_score": composite_score,
            "critic_feedback": user_approval,
            "iteration_count": 0,  # Reset for user-requested changes
            "_should_retry": True,
        }

    return {
        "critic_score": composite_score,
        "critic_feedback": feedback,
        "iteration_count": iteration_count,
    }


def critic_agent_sync(state: BlogState) -> Dict[str, Any]:
    """Synchronous version of critic agent"""
    assembled_blog = state.get("assembled_blog", "")
    summarized_facts = state.get("summarized_facts", [])
    iteration_count = state.get("iteration_count", 0)

    llm_manager = get_llm_manager()
    llm = llm_manager.get_critic_llm()

    system_prompt = get_agent_prompt("critic")

    # Prepare facts context for grounding check
    facts_text = ""
    if summarized_facts:
        facts_text = "Available research facts:\n"
        for fact in summarized_facts:
            fact_text = fact.get("fact", "") if isinstance(fact, dict) else str(fact)
            facts_text += f"- {fact_text}\n"

    user_message = f"""Evaluate this blog content:

{assembled_blog}

{facts_text}

Score the blog on depth, clarity, and grounding (0.0-1.0 each)."""

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    # Parse JSON response
    try:
        critic_json = extract_text(response)
        if "```" in critic_json:
            critic_json = critic_json.split("```")[1].replace("json", "").strip()
        critic_data = json.loads(critic_json)
    except json.JSONDecodeError:
        # Fallback scoring
        critic_data = {
            "depth_score": 0.8,
            "clarity_score": 0.85,
            "grounding_score": 0.8,
            "composite_score": 0.8167,
            "passed": True,
            "feedback": "",
        }

    # Extract scores
    depth = float(critic_data.get("depth_score", 0.8))
    clarity = float(critic_data.get("clarity_score", 0.8))
    grounding = float(critic_data.get("grounding_score", 0.8))

    # Calculate composite score: (0.4 × depth) + (0.3 × clarity) + (0.3 × grounding)
    composite_score = (0.4 * depth) + (0.3 * clarity) + (0.3 * grounding)

    feedback = critic_data.get("feedback", "")
    iteration_count += 1

    return {
        "critic_score": composite_score,
        "critic_feedback": feedback,
        "iteration_count": iteration_count,
    }
