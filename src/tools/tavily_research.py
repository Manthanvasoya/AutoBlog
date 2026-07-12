"""
Tavily API wrapper for internet research.
Clean, LLM-optimized API that returns pre-extracted text.
"""

from typing import List, Dict, Any, Optional
import requests
from src.core.config import get_app_settings


class TavilyResearchTool:
    """Tavily Search API client"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tavily client"""
        settings = get_app_settings()
        self.api_key = api_key or settings.tavily_api_key
        self.base_url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using Tavily API.

        Args:
            query: Search query
            max_results: Max results to return

        Returns:
            List of cleaned search results
        """
        if not self.api_key:
            raise ValueError("Tavily API key not set")

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,  # Get cleaned content only
        }

        response = requests.post(self.base_url, json=payload)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        # Clean and format results
        cleaned = []
        for result in results:
            cleaned.append(
                {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                }
            )

        return cleaned

    def search_multiple(self, queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search multiple queries and combine results.

        Args:
            queries: List of search queries

        Returns:
            Dict mapping query -> results
        """
        all_results = {}
        for query in queries:
            all_results[query] = self.search(query)
        return all_results


def search_tavily(queries: List[str], max_results_per_query: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """Convenient function to search Tavily"""
    tool = TavilyResearchTool()
    results = {}
    for query in queries:
        results[query] = tool.search(query, max_results_per_query)
    return results
