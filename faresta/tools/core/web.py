import httpx
from ..base import Tool


class WebFetchTool(Tool):
    name = "web_fetch"
    description = "Fetch content from a URL. Returns the page content as markdown or text."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch content from",
            },
            "format": {
                "type": "string",
                "enum": ["markdown", "text"],
                "description": "Output format (default: markdown)",
            },
        },
        "required": ["url"],
    }

    def execute(self, url: str, format: str = "markdown") -> str:
        try:
            with httpx.Client(follow_redirects=True, timeout=30) as client:
                resp = client.get(url, headers={"User-Agent": "FarestaCode/1.0"})
                resp.raise_for_status()
                text = resp.text
                if len(text) > 50000:
                    text = text[:50000] + "\n... [truncated at 50000 chars]"
                return text
        except httpx.HTTPStatusError as e:
            return f"HTTP error fetching {url}: {e.response.status_code}"
        except httpx.TimeoutException:
            return f"Error: timeout fetching {url}"
        except Exception as e:
            return f"Error fetching {url}: {e}"


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information. Returns search results with titles and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "count": {
                "type": "integer",
                "description": "Number of results to return (default: 5)",
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, count: int = 5) -> str:
        try:
            with httpx.Client(follow_redirects=True, timeout=15) as client:
                search_url = f"https://html.duckduckgo.com/html/?q={httpx.utils.quote(query)}"
                resp = client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()

                import re
                results = []
                for item in re.finditer(
                    r'<a rel="nofollow" class="result__a" href="(.*?)">.*?<b>(.*?)</b>',
                    resp.text,
                ):
                    url = item.group(1)
                    title = re.sub(r"<[^>]+>", "", item.group(2)).strip()
                    results.append(f"{title}\n  {url}")

                if not results:
                    return f"No results found for '{query}'"

                return "\n\n".join(results[:count])
        except Exception as e:
            return f"Error searching: {e}"