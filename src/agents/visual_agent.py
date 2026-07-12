"""
Visual Agent — Generates charts and cover images for the blog.
Runs in parallel with SEO agent.
Uses Matplotlib for charts, DALL-E for cover image.
"""

import json
from typing import Dict, Any, List
from src.core.state import BlogState, ChartPath
from src.llm.prompts import get_agent_prompt
from src.llm.models import get_llm_manager


def visual_agent(state: BlogState) -> Dict[str, Any]:
    """
    Generate visual assets: charts for sections and cover image.

    Reads: outline (sections with visual metadata), topic, tone
    Writes: chart_paths, cover_image_path
    Parallel: Runs simultaneously with SEO agent
    """

    outline = state.get("outline", {})
    topic = state.get("topic", "")
    tone = state["plan"].get("tone", "professional")

    # For now, create placeholder paths
    # In production, this would call Matplotlib and DALL-E APIs
    chart_paths: List[ChartPath] = []

    for section in outline.get("sections", []):
        if section.get("needs_visual", False):
            heading = section.get("heading", "Chart")
            # Placeholder: in production, generate actual chart
            chart_path = f"data/charts/{heading.lower().replace(' ', '_')}.png"
            chart_paths.append({"section_heading": heading, "path": chart_path})

    # Placeholder cover image path
    cover_image_path = "data/covers/cover_image.png"

    return {
        "chart_paths": chart_paths,
        "cover_image_path": cover_image_path,
    }
