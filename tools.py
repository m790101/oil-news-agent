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




# ── Soros portfolio save tool ───────────────────────────────────────────────
 
def save_soros_holding(
    rank: int,
    ticker: str,
    company: str,
    sector: str,
    instrument_type: str,
    value_usd: str,
    portfolio_pct: str,
    change_note: str,
    source: str,
) -> str:
    """Save a single Soros Fund Management portfolio holding to the database.
    Call this once per holding after searching for the latest 13F filing.
    Args:
        rank: position rank (1 = largest holding)
        ticker: stock ticker symbol e.g. 'GOOGL'
        company: full company name e.g. 'Alphabet Inc'
        sector: industry sector e.g. 'Technology'
        instrument_type: type of instrument — must be one of:
            'stock'   → regular equity/stock
            'etf'     → exchange traded fund
            'put'     → put option (bearish/hedge position)
            'call'    → call option (bullish position)
            'warrant' → warrant
        value_usd: market value as string e.g. '$500M' or '$1.2B'
        portfolio_pct: percentage of portfolio e.g. '12.5%'
        change_note: one of 'new position', 'increased', 'decreased', 'unchanged'
        source: URL or name of the source
    """
    from db import insert_soros_holding
    insert_soros_holding(rank, ticker, company, sector, instrument_type, value_usd, portfolio_pct, change_note, source)
    return f"Saved #{rank}: [{instrument_type.upper()}] {ticker} - {company} ({portfolio_pct})"
 
 
save_soros_tool = FunctionTool.from_defaults(fn=save_soros_holding)