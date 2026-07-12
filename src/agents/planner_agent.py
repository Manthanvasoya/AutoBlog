"""
Planner Agent — First node in the blog generation pipeline.
Analyzes topic and creates a comprehensive plan.
Includes HITL checkpoint for user approval.
"""

import json
from typing import Dict, Any
from langgraph.types import interrupt
from src.core.state import BlogState
from src.llm.prompts import get_agent_prompt
from src.llm.models import get_llm_manager
from src.utils.llm_helpers import extract_text


async def planner_agent(state: BlogState) -> Dict[str, Any]:
    """
    Plan the blog structure and decide if research is needed.

    Reads: topic
    Writes: plan
    HITL: Yes (embedded interrupt for user approval)
    """

    topic = state["topic"]
    llm_manager = get_llm_manager()
    llm = llm_manager.get_planner_llm()

    # Get system prompt
    system_prompt = get_agent_prompt("planner")

    # Create planning request
    user_message = f"Create a comprehensive blog plan for the topic: {topic}"

    # Call LLM for planning
    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    # Parse JSON response
    try:
        plan_json = extract_text(response)
        # Extract JSON if wrapped in markdown code block
        if "```" in plan_json:
            plan_json = plan_json.split("```")[1].replace("json", "").strip()
        plan = json.loads(plan_json)
    except json.JSONDecodeError as e:
        # Fallback: regenerate with stricter instructions
        return {
            "plan": {
                "target_audience": "general",
                "tone": "informative",
                "needs_research": True,
                "research_queries": [topic],
                "outline_hints": ["Introduction", "Main Content", "Conclusion"],
                "visual_requirements": [],
            }
        }

    # HITL Checkpoint 1: User approves or rejects the plan
    # interrupt() pauses the graph and waits for user response
    user_feedback = interrupt(
        {
            "checkpoint": "planner",
            "plan": plan,
            "message": "Review and approve the blog plan",
        }
    )

    # If user provided feedback, regenerate with feedback
    if user_feedback and isinstance(user_feedback, str):
        refinement_prompt = f"""The user provided this feedback on the plan: {user_feedback}

Please regenerate the plan incorporating this feedback. Output updated JSON with same fields."""

        response = llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": refinement_prompt},
            ]
        )

        try:
            plan_json = extract_text(response)
            if "```" in plan_json:
                plan_json = plan_json.split("```")[1].replace("json", "").strip()
            plan = json.loads(plan_json)
        except json.JSONDecodeError:
            pass  # Keep original plan if parsing fails

    return {"plan": plan}


# For testing without async
def planner_agent_sync(state: BlogState) -> Dict[str, Any]:
    """Synchronous version of planner agent"""
    topic = state["topic"]
    llm_manager = get_llm_manager()
    llm = llm_manager.get_planner_llm()

    system_prompt = get_agent_prompt("planner")
    user_message = f"Create a comprehensive blog plan for the topic: {topic}"

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    try:
        plan_json = extract_text(response)
        if "```" in plan_json:
            plan_json = plan_json.split("```")[1].replace("json", "").strip()
        plan = json.loads(plan_json)
    except json.JSONDecodeError:
        plan = {
            "target_audience": "general",
            "tone": "informative",
            "needs_research": True,
            "research_queries": [topic],
            "outline_hints": ["Introduction", "Main Content", "Conclusion"],
            "visual_requirements": [],
        }

    return {"plan": plan}
