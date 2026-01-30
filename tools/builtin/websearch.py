"""
Web Search Tool - Multi-engine with automatic fallback
Linus: Simple tools that do one thing well

Supported engines:
- DuckDuckGo: Free, no API key required (default fallback)
- Serper: Google Search API, needs SERPER_API_KEY
- Tavily: AI-optimized search, needs TAVILY_API_KEY
"""

import os
import re
import asyncio
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..pure_base import PureTool
from core.logger import log

if TYPE_CHECKING:
    from core.types import TaskContext


@dataclass
class SearchResult:
    """Single search result."""
    title: str
    url: str
    snippet: str
    position: int


class SearchEngine(ABC):
    """Abstract base class for search engines."""
    
    name: str = "base"
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Execute search and return results."""
        pass
    
    def is_available(self) -> bool:
        """Check if this engine is available (has required credentials)."""
        return True


class DuckDuckGoEngine(SearchEngine):
    """DuckDuckGo search engine - free, no API key required."""
    
    name = "duckduckgo"
    
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Search using DuckDuckGo HTML endpoint."""
        import httpx
        
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data={"q": query},
                headers=headers,
                follow_redirects=True,
                timeout=10.0
            )
            response.raise_for_status()
            
            return self._parse_html(response.text, num_results)
    
    def _parse_html(self, html: str, num_results: int) -> List[SearchResult]:
        """Parse DuckDuckGo HTML response."""
        results = []
        
        # Pattern to extract result blocks
        # DuckDuckGo uses class="result" for each result
        result_pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>',
            re.DOTALL | re.IGNORECASE
        )
        
        # Alternative simpler pattern
        link_pattern = re.compile(
            r'<a[^>]*rel="nofollow"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>',
            re.IGNORECASE
        )
        snippet_pattern = re.compile(
            r'class="result__snippet"[^>]*>([^<]*)<',
            re.IGNORECASE
        )
        
        # Try to extract results
        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)
        
        for i, (url, title) in enumerate(links[:num_results]):
            if url.startswith('//duckduckgo.com/l/?'):
                # Extract actual URL from DDG redirect
                actual_url_match = re.search(r'uddg=([^&]+)', url)
                if actual_url_match:
                    from urllib.parse import unquote
                    url = unquote(actual_url_match.group(1))
            
            snippet = snippets[i] if i < len(snippets) else ""
            
            results.append(SearchResult(
                title=title.strip(),
                url=url,
                snippet=snippet.strip(),
                position=i + 1
            ))
        
        return results


class SerperEngine(SearchEngine):
    """Serper.dev Google Search API."""
    
    name = "serper"
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Search using Serper API."""
        import httpx
        
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            return self._parse_response(data)
    
    def _parse_response(self, data: Dict) -> List[SearchResult]:
        """Parse Serper API response."""
        results = []
        
        for i, item in enumerate(data.get("organic", [])):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=i + 1
            ))
        
        return results


class TavilyEngine(SearchEngine):
    """Tavily AI-optimized search API."""
    
    name = "tavily"
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Search using Tavily API."""
        import httpx
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": num_results,
            "include_answer": False,
            "include_raw_content": False
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
            
            return self._parse_response(data)
    
    def _parse_response(self, data: Dict) -> List[SearchResult]:
        """Parse Tavily API response."""
        results = []
        
        for i, item in enumerate(data.get("results", [])):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                position=i + 1
            ))
        
        return results


class Tool(PureTool):
    """Web Search Tool - Multi-engine with automatic fallback."""
    
    def __init__(self):
        """Initialize websearch tool with available engines."""
        super().__init__()
        self.name = "websearch"
        
        # Initialize engines in priority order
        self._engines: List[SearchEngine] = [
            SerperEngine(),    # Preferred: Google results via API
            TavilyEngine(),    # Secondary: AI-optimized
            DuckDuckGoEngine() # Fallback: Always available
        ]
    
    @property
    def definition(self) -> Dict:
        """Tool definition - OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": "websearch",
                "description": "Search the web for real-time information. Returns titles, URLs, and snippets from search results. Automatically falls back to alternative search engines if primary fails.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to submit"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5, max: 10)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional["TaskContext"] = None
    ) -> Dict:
        """Execute web search with automatic fallback.

        Args:
            parameters: Contains 'query' and optional 'num_results'
            context: Task context (unused for websearch)

        Returns:
            Dict with success status and search results
        """
        query = parameters.get("query", "").strip()
        num_results = min(parameters.get("num_results", 5), 10)

        if not query:
            return {"success": False, "error": "No search query provided"}

        try:
            return await self._search_with_fallback(query, num_results)
        except Exception as e:
            log.error(f"Web search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _search_with_fallback(
        self,
        query: str,
        num_results: int
    ) -> Dict:
        """Execute search with automatic engine fallback."""
        errors = []
        
        for engine in self._engines:
            if not engine.is_available():
                log.debug(f"Search engine {engine.name} not available (missing API key)")
                continue

            try:
                log.step(f"Searching with {engine.name}")
                results = await engine.search(query, num_results)
                
                if results:
                    return self._format_results(query, results, engine.name)
                else:
                    errors.append(f"{engine.name}: No results")
                    
            except Exception as e:
                error_msg = f"{engine.name}: {str(e)}"
                errors.append(error_msg)
                log.warning(f"Search engine {engine.name} failed: {e}")
                continue
        
        # All engines failed
        return {
            "success": False,
            "error": f"All search engines failed: {'; '.join(errors)}",
            "query": query
        }
    
    def _format_results(
        self,
        query: str,
        results: List[SearchResult],
        engine: str
    ) -> Dict:
        """Format search results for output."""
        formatted_results = []
        
        for r in results:
            formatted_results.append({
                "position": r.position,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet
            })
        
        # Create human-readable summary
        summary_lines = [f"Search results for: '{query}' (via {engine})"]
        for r in results:
            summary_lines.append(f"\n{r.position}. {r.title}")
            summary_lines.append(f"   URL: {r.url}")
            if r.snippet:
                summary_lines.append(f"   {r.snippet[:200]}")
        
        return {
            "success": True,
            "query": query,
            "engine": engine,
            "count": len(results),
            "results": formatted_results,
            "summary": "\n".join(summary_lines)
        }
