import os
import requests
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

NEWS_API_BASE = "https://newsapi.org/v2"

CATEGORY_MAP = {
    "technology": "technology",
    "finance": "business",
    "sports": "sports",
    "health": "health",
    "science": "science",
    "entertainment": "entertainment",
    "general": "general",
}


def _newsapi_key() -> str:
    return os.getenv("NEWS_API_KEY", "")


def _is_newsapi_configured() -> bool:
    key = _newsapi_key()
    return bool(key and key != "your_newsapi_key_here")


def _format_articles(articles: list, label: str) -> str:
    if not articles:
        return f"No articles found for {label}."
    out = f"**{label}**\n\n"
    for i, a in enumerate(articles[:5], 1):
        title = a.get("title") or "No title"
        source = (a.get("source") or {}).get("name", "Unknown")
        desc = a.get("description") or ""
        published = (a.get("publishedAt") or "")[:10]
        url = a.get("url") or ""
        out += f"{i}. **{title}**\n"
        out += f"   Source: {source} | Published: {published}\n"
        if desc:
            out += f"   {desc}\n"
        if url:
            out += f"   [Read more]({url})\n"
        out += "\n"
    return out


@tool
def get_top_headlines(category: str) -> str:
    """Fetch top headlines for a news category. Valid categories: technology, finance, sports, health, science, entertainment, general."""
    mapped = CATEGORY_MAP.get(category.lower(), "general")

    if _is_newsapi_configured():
        try:
            resp = requests.get(
                f"{NEWS_API_BASE}/top-headlines",
                params={
                    "category": mapped,
                    "language": "en",
                    "pageSize": 5,
                    "apiKey": _newsapi_key(),
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "ok" and data.get("articles"):
                return _format_articles(data["articles"], f"Top {category.title()} Headlines")
            error = data.get("message", "No articles returned")
        except Exception as e:
            error = str(e)

        # Fallback to web search on NewsAPI failure
        try:
            ddg = DuckDuckGoSearchRun()
            return f"[NewsAPI fallback]\n\n" + ddg.run(f"latest {category} news today")
        except Exception:
            return f"Could not fetch {category} news. NewsAPI error: {error}"

    # No NewsAPI key — use web search directly
    try:
        ddg = DuckDuckGoSearchRun()
        return f"[Web search — add NEWS_API_KEY for richer results]\n\n" + ddg.run(
            f"latest {category} news today"
        )
    except Exception as e:
        return f"Web search failed: {str(e)}"


@tool
def search_news_by_keyword(query: str) -> str:
    """Search for recent news articles matching a specific keyword or topic."""
    if _is_newsapi_configured():
        try:
            resp = requests.get(
                f"{NEWS_API_BASE}/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                    "apiKey": _newsapi_key(),
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "ok" and data.get("articles"):
                return _format_articles(data["articles"], f"News about '{query}'")
        except Exception:
            pass

    # Fallback
    try:
        ddg = DuckDuckGoSearchRun()
        return ddg.run(f"{query} news latest")
    except Exception as e:
        return f"Search failed: {str(e)}"


@tool
def web_search(query: str) -> str:
    """Search the web for general information, facts, or context that supplements news coverage."""
    try:
        ddg = DuckDuckGoSearchRun()
        return ddg.run(query)
    except Exception as e:
        return f"Web search unavailable: {str(e)}"


news_tools = [get_top_headlines, search_news_by_keyword]
general_tools = [web_search]
all_tools = [get_top_headlines, search_news_by_keyword, web_search]
