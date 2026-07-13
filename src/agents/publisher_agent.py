"""
Publisher Agent — Publishes to Dev.to and Medium.
Dev.to first (synchronous, returns URL immediately).
Medium second (sets canonical URL to Dev.to).
"""

from typing import Dict, Any
from src.core.state import BlogState
from src.tools.devto_publisher import publish_to_devto as publish_to_devto_api
from src.tools.medium_publisher import publish_to_medium as publish_to_medium_api
from src.database.mongodb_client import create_mongodb_client
from src.core.config import get_app_settings, get_app_config


def publisher_agent(state: BlogState) -> Dict[str, Any]:
    """
    Publish blog to Dev.to and Medium.

    Reads: assembled_blog, cover_image_path, seo_tags, meta_description, slug, outline.title
    Writes: devto_url, medium_url, published
    """

    assembled_blog = state.get("assembled_blog", "")
    cover_image_path = state.get("cover_image_path", "")
    seo_tags = state.get("seo_tags", [])
    meta_description = state.get("meta_description", "")
    slug = state.get("slug", "")
    title = state.get("outline", {}).get("title", "")

    if not assembled_blog or not title:
        return {
            "devto_url": "",
            "medium_url": "",
            "published": False,
        }

    # Get user's platform choices (default to True for backward compatibility)
    publish_to_devto = state.get("publish_to_devto", True)
    publish_to_medium = state.get("publish_to_medium", True)

    devto_url = ""
    medium_url = ""
    published = False

    try:
        # Publish to Dev.to first (synchronous) — only if user selected it
        if publish_to_devto:
            try:
                # Dev.to expects a public URL for cover images, not a local file path
                cover_url = cover_image_path if cover_image_path and cover_image_path.startswith("http") else None
                
                devto_url = publish_to_devto_api(
                    title=title,
                    markdown=assembled_blog,
                    tags=seo_tags,
                    description=meta_description,
                    cover_image_url=cover_url,
                )
            except Exception as e:
                print(f"Dev.to publishing failed: {e}")
                devto_url = ""

        # Publish to Medium second (with canonical URL) — only if user selected it
        if publish_to_medium:
            try:
                medium_url = publish_to_medium_api(
                    title=title,
                    markdown_content=assembled_blog,
                    tags=seo_tags,
                    canonical_url=devto_url if devto_url else None,
                )
            except Exception as e:
                print(f"Medium publishing failed: {e}")
                medium_url = ""

        # Consider published if at least one platform succeeded
        published = bool(devto_url or medium_url)

        # Save to MongoDB
        try:
            settings = get_app_settings()
            client = create_mongodb_client(
                settings.mongodb_uri,
                settings.mongodb_database,
            )

            blog_record = {
                "topic": state.get("topic", ""),
                "title": title,
                "devto_url": devto_url,
                "medium_url": medium_url,
                "critic_score": state.get("critic_score", 0.0),
                "word_count": len(assembled_blog.split()),
                "section_count": len(state.get("outline", {}).get("sections", [])),
                "published": published,
                "publish_timestamp": None if not published else "datetime.utcnow()",
            }

            client.save_blog(blog_record)
            client.disconnect()
        except Exception as e:
            print(f"MongoDB save failed: {e}")

    except Exception as e:
        print(f"Publisher agent failed: {e}")

    return {
        "devto_url": devto_url,
        "medium_url": medium_url,
        "published": published,
    }
