"""
Assembler Node — Pure Python, no LLM.
Combines draft + charts + SEO frontmatter into final publishable markdown.
Critic evaluates this assembled blog, not the raw draft.
"""

import re
from typing import Dict, Any
from src.core.state import BlogState


def assembler_node(state: BlogState) -> Dict[str, Any]:
    """
    Assemble final blog: SEO frontmatter + draft + embedded charts.

    Reads: draft, chart_paths, cover_image_path, seo_tags, meta_description, slug, outline.title
    Writes: assembled_blog
    Pure Python: No LLM calls, deterministic formatting
    """

    draft = state.get("draft", "")
    chart_paths = state.get("chart_paths", [])
    cover_image_path = state.get("cover_image_path", "")
    seo_tags = state.get("seo_tags", [])
    meta_description = state.get("meta_description", "")
    slug = state.get("slug", "")
    title = state.get("outline", {}).get("title", "")
    outline = state.get("outline", {})

    import re
    # Clean tags for frontmatter (Dev.to parses this and throws 422 if invalid)
    clean_tags = []
    for t in seo_tags:
        clean = re.sub(r'[^a-zA-Z0-9]', '', str(t)).lower()
        if clean:
            clean_tags.append(clean)
    clean_tags = clean_tags[:4]

    # Only include cover image in frontmatter if it's a public URL
    cover_line = f"\ncover_image: {cover_image_path}" if cover_image_path and cover_image_path.startswith("http") else ""

    # Step 1: Build SEO frontmatter
    frontmatter = f"""---
title: {title}
description: {meta_description}
tags: {", ".join(clean_tags)}
slug: {slug}{cover_line}
---"""

    # Step 2: Embed charts into draft
    # Split draft into sections by heading level
    assembled_content = frontmatter + "\n\n"

    # Add cover image reference if available
    if cover_image_path:
        assembled_content += f"![Cover]({cover_image_path})\n\n"

    # Add draft content
    assembled_content += draft

    # Step 3: Inject charts at appropriate section positions
    # For each chart, find matching section heading and embed image after it
    for chart in chart_paths:
        section_heading = chart.get("section_heading", "")
        chart_path = chart.get("path", "")

        # Find the section heading in assembled content
        # Look for markdown heading pattern (## or #)
        heading_pattern = rf"^(#{2,6})\s+{re.escape(section_heading)}\s*$"

        # Find and replace
        def add_chart(match):
            heading = match.group(0)
            # Add chart image after the heading
            return f"{heading}\n\n![{section_heading}]({chart_path})"

        assembled_content = re.sub(
            heading_pattern,
            add_chart,
            assembled_content,
            flags=re.MULTILINE,
            count=1,
        )

    return {"assembled_blog": assembled_content}
