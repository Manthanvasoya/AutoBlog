"""
Research Agent — Conducts internet research via Tavily API.
Only runs if Planner sets needs_research=True.
Extracts key facts, not full articles.
"""

import json
from typing import Dict, Any, List
from src.core.state import BlogState, ResearchFactDict
from src.llm.prompts import get_agent_prompt
from src.llm.models import get_llm_manager
from src.utils.llm_helpers import extract_text
from src.tools.tavily_research import search_tavily


def research_agent(state: BlogState) -> Dict[str, Any]:
    """
    Conduct internet research and extract key facts.

    Reads: plan.research_queries
    Writes: summarized_facts
    Constraint: Only extracted facts, never full articles
    """

    research_queries = state["plan"].get("research_queries", [])

    if not research_queries:
        return {"summarized_facts": []}

    # Search Tavily for all queries
    try:
        search_results = search_tavily(research_queries, max_results_per_query=5)
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return {"summarized_facts": []}

    # Now extract facts from results using LLM
    llm_manager = get_llm_manager()
    llm = llm_manager.get_research_llm()

    system_prompt = get_agent_prompt("research")

    # Prepare search results text
    results_text = ""
    for query, results in search_results.items():
        results_text += f"\n## Research for: {query}\n"
        for i, result in enumerate(results, 1):
            results_text += f"\n### Result {i}: {result.get('title', 'No title')}\n"
            results_text += f"Source: {result.get('url', '')}\n"
            results_text += f"Content: {result.get('content', '')}\n"

    user_message = f"Extract key facts from these research results:\n{results_text}"

    # Call LLM to extract facts
    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    # Parse JSON response
    try:
        facts_json = extract_text(response)
        # Extract JSON from markdown code block if present
        if "```" in facts_json:
            facts_json = facts_json.split("```")[1].replace("json", "").strip()
        summarized_facts = json.loads(facts_json)
    except json.JSONDecodeError:
        summarized_facts = []

    return {"summarized_facts": summarized_facts}
