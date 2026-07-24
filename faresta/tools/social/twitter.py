import os
import httpx
from ..base import Tool


class TwitterTool(Tool):
    name = "twitter"
    description = "Post tweets and search Twitter/X. Requires TWITTER_BEARER_TOKEN env var for search, TWITTER_API_KEY + TWITTER_API_SECRET + TWITTER_ACCESS_TOKEN + TWITTER_ACCESS_SECRET for posting."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["post", "search"],
                "description": "Action: 'post' to tweet, 'search' to find tweets",
            },
            "text": {
                "type": "string",
                "description": "Tweet text (required for post action)",
            },
            "query": {
                "type": "string",
                "description": "Search query (required for search action)",
            },
            "count": {
                "type": "integer",
                "description": "Number of search results (default: 5)",
            },
        },
        "required": ["action"],
    }

    def execute(self, action: str, text: str = "", query: str = "", count: int = 5) -> str:
        if action == "post":
            return self._post_tweet(text)
        elif action == "search":
            return self._search_tweets(query, count)
        return f"Unknown action: {action}"

    def _post_tweet(self, text: str) -> str:
        if not text:
            return "Error: text is required for posting"
        api_key = os.getenv("TWITTER_API_KEY", "")
        api_secret = os.getenv("TWITTER_API_SECRET", "")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        access_secret = os.getenv("TWITTER_ACCESS_SECRET", "")
        bearer = os.getenv("TWITTER_BEARER_TOKEN", "")

        if bearer:
            try:
                with httpx.Client() as client:
                    resp = client.post(
                        "https://api.twitter.com/2/tweets",
                        json={"text": text},
                        headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"},
                    )
                    if resp.status_code == 201:
                        data = resp.json()
                        tweet_id = data.get("data", {}).get("id", "unknown")
                        return f"Tweet posted successfully! ID: {tweet_id}"
                    return f"Error posting tweet: {resp.status_code} - {resp.text}"
            except Exception as e:
                return f"Error posting tweet: {e}"

        return "Error: Twitter posting requires OAuth 2.0 Bearer token with write scope. Set TWITTER_BEARER_TOKEN."

    def _search_tweets(self, query: str, count: int) -> str:
        if not query:
            return "Error: query is required for search"
        bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
        if not bearer:
            return "Error: TWITTER_BEARER_TOKEN not set"

        try:
            with httpx.Client() as client:
                resp = client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    params={"query": query, "max_results": min(count, 10)},
                    headers={"Authorization": f"Bearer {bearer}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    tweets = data.get("data", [])
                    if not tweets:
                        return f"No tweets found for '{query}'"
                    results = []
                    for t in tweets:
                        results.append(f"• {t.get('text', '').strip()[:200]}")
                    return f"Search results for '{query}':\n" + "\n".join(results)
                return f"Error searching tweets: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"Error searching tweets: {e}"
