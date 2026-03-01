import os
import json
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from llama_index.core.tools import FunctionTool
from db import insert_crude_oil, insert_taiwan_law

load_dotenv()


# ── Shared search function ──────────────────────────────────────────────────

async def search_web(query: str) -> str:
    """Search the web for current information based on a query string. 
    Returns a list of results with title, url, content, and source."""
    print(f"[TOOL] search_web called with query: '{query}'")
    client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    result = await client.search(query, max_results=5)
    return json.dumps(result, ensure_ascii=False)


# ── Crude oil save tool ─────────────────────────────────────────────────────

def save_crude_oil_news(title: str, summary: str, url: str, source: str) -> str:
    """Save a crude oil news item to the database.
    Call this after searching to persist each relevant result.
    Args:
        title: headline of the news article
        summary: 2-3 sentence summary of the article content
        url: full URL of the article
        source: name of the publication or website
    """
    insert_crude_oil(title=title, summary=summary, url=url, source=source)
    return f"Saved: {title}"


# ── Taiwan futures law save tool ────────────────────────────────────────────

def save_taiwan_law(
    title: str,
    content: str,
    url: str,
    source: str,
    category: str,
    relevance_score: float,
) -> str:
    """Save a Taiwan futures law or regulation item to the database.
    Call this after searching to persist each relevant result.
    Args:
        title: title of the law, regulation, or announcement
        content: full content or detailed summary of the item
        url: full URL of the source
        source: name of the publication, government body, or website
        category: classify as one of: 'regulation', 'announcement', 'ruling', 'amendment', 'guideline'
        relevance_score: float between 0.0 and 1.0 rating how relevant this is to Taiwan futures trading law
    """
    print("==== law save to db ======")
    insert_taiwan_law(
        title=title,
        content=content,
        url=url,
        source=source,
        category=category,
        relevance_score=relevance_score,
    )
    return f"Saved: {title} | category={category} | score={relevance_score}"


# ── LlamaIndex FunctionTool wrappers ────────────────────────────────────────

search_tool = FunctionTool.from_defaults(fn=search_web)
save_crude_oil_tool = FunctionTool.from_defaults(fn=save_crude_oil_news)
save_taiwan_law_tool = FunctionTool.from_defaults(fn=save_taiwan_law)