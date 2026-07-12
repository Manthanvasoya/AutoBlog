"""
Dev.to API integration for publishing blogs.
Dev.to returns live URL immediately upon posting.
"""

from typing import Dict, Any, Optional, List
import requests
from src.core.config import get_app_settings


class DevToPublisher:
    """Dev.to API client for publishing"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Dev.to client"""
        settings = get_app_settings()
        self.api_key = api_key or settings.devto_api_key
        self.base_url = "https://dev.to/api/articles"

    def publish(
        self,
        title: str,
        markdown: str,
        tags: List[str],
        description: str,
        cover_image_url: Optional[str] = None,
        canonical_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish an article to Dev.to.

        Args:
            title: Article title
            markdown: Article content in markdown
            tags: List of tags
            description: Article description
            cover_image_url: URL to cover image
            canonical_url: Canonical URL (for cross-posting)

        Returns:
            Published article data with live URL
        """
        if not self.api_key:
            raise ValueError("Dev.to API key not set")

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        # Limit tags to 5
        tags = tags[:5]

        article_data = {
            "article": {
                "title": title,
                "published": True,
                "body_markdown": markdown,
                "tags": tags,
                "description": description,
            }
        }

        if cover_image_url:
            article_data["article"]["cover_image_url"] = cover_image_url

        if canonical_url:
            article_data["article"]["canonical_url"] = canonical_url

        response = requests.post(self.base_url, json=article_data, headers=headers)
        response.raise_for_status()

        published_article = response.json()
        return {
            "url": published_article.get("url", ""),
            "id": published_article.get("id", ""),
            "title": published_article.get("title", ""),
        }


def publish_to_devto(
    title: str,
    markdown: str,
    tags: list,
    description: str,
    cover_image_url: Optional[str] = None,
) -> str:
    """Convenient function to publish to Dev.to. Returns live URL."""
    publisher = DevToPublisher()
    result = publisher.publish(title, markdown, tags, description, cover_image_url)
    return result["url"]
