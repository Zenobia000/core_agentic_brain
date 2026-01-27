# tools/web_search.py
import httpx
from core.tool_manager import register_tool

# Note: This is a simple example using DuckDuckGo's HTML endpoint.
# For a real application, you would want to use a proper search API 
# (e.g., Google Custom Search, Bing Search, Serper.dev) and parse the results
# more robustly, possibly with a library like BeautifulSoup.

@register_tool
def web_search(query: str) -> str:
    """
    Performs a web search using DuckDuckGo and returns the raw HTML result.

    Args:
        query: The search query.

    Returns:
        A snippet of the HTML response or an error message.
    """
    if not query:
        return "Error: No search query provided."

    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    try:
        with httpx.Client() as client:
            response = client.get(url, params=params, headers=headers, follow_redirects=True)
            response.raise_for_status() # Raise an exception for bad status codes
            
            # For simplicity, we return the first 2000 characters of the text.
            # A real implementation should parse the HTML to extract relevant snippets.
            return response.text[:2000]

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP request failed with status code {e.response.status_code}."
    except httpx.RequestError as e:
        return f"Error: An error occurred while making the web request: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
