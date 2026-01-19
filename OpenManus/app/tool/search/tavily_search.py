import os
from typing import List

from tavily import TavilyClient

from app.logger import logger
from app.tool.search.base import SearchItem, WebSearchEngine


class TavilySearchEngine(WebSearchEngine):
    """A search engine that uses the Tavily API."""

    client: TavilyClient = None

    def __init__(self):
        super().__init__()
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set.")
        self.client = TavilyClient(api_key=api_key)

    def perform_search(
        self, query: str, num_results: int = 5, *args, **kwargs
    ) -> List[SearchItem]:
        """
        Perform a web search using the Tavily API.

        Args:
            query: The search query.
            num_results: The number of results to return.

        Returns:
            A list of SearchItem objects.
        """
        try:
            # Tavily's search method uses 'max_results' instead of 'num_results'
            response = self.client.search(
                query=query, search_depth="basic", max_results=num_results
            )
            results = response.get("results", [])

            search_items = [
                SearchItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    description=item.get("content", ""),
                )
                for item in results
            ]
            return search_items
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
