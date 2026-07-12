"""
Medium API integration for publishing blogs.
Sets canonical URL to original Dev.to post to avoid duplicate content penalty.
"""

from typing import Dict, Any, Optional
import requests
import markdown
from src.core.config import get_app_settings


class MediumPublisher:
    """Medium API client for publishing"""

    def __init__(self, access_token: Optional[str] = None, user_id: Optional[str] = None):
        """Initialize Medium client"""
        settings = get_app_settings()
        self.access_token = access_token or settings.medium_access_token
        self.user_id = user_id or settings.medium_user_id
        self.base_url = "https://api.medium.com/v1"

    def publish(
        self,
        title: str,
        html_content: str,
        tags: list,
        canonical_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish an article to Medium.

        Args:
            title: Article title
            html_content: Article content in HTML
            tags: List of tags
            canonical_url: Canonical URL (usually the Dev.to URL)

        Returns:
            Published article data
        """
        if not self.access_token or not self.user_id:
            raise ValueError("Medium access token or user ID not set")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Limit tags to 5
        tags = tags[:5]

        url = f"{self.base_url}/users/{self.user_id}/posts"

        post_data = {
            "title": title,
            "contentFormat": "html",
            "content": html_content,
            "tags": tags,
            "publishStatus": "public",
        }

        if canonical_url:
            post_data["canonicalUrl"] = canonical_url

        response = requests.post(url, json=post_data, headers=headers)
        response.raise_for_status()

        published_post = response.json()
        return {
            "url": published_post.get("url", ""),
            "id": published_post.get("id", ""),
            "title": published_post.get("title", ""),
        }


def convert_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML for Medium"""
    return markdown.markdown(markdown_text)


def publish_to_medium(
    title: str,
    markdown_content: str,
    tags: list,
    canonical_url: str,
) -> str:
    """Convenient function to publish to Medium. Returns live URL."""
    html_content = convert_markdown_to_html(markdown_content)
    publisher = MediumPublisher()
    result = publisher.publish(title, html_content, tags, canonical_url)
    return result["url"]
