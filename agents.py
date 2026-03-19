import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from tools import search_tool, save_crude_oil_tool, save_taiwan_law_tool, save_soros_tool, save_daily_news_tool

load_dotenv()

llm = OpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY", ""))


def build_crude_oil_agent() -> FunctionAgent:
    """Agent that searches for crude oil news and saves results to DB."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return FunctionAgent(
        tools=[search_tool, save_crude_oil_tool],
        llm=llm,
        verbose=True,
        system_prompt=f"""You are a crude oil market research agent.
        today is {current_date}, year is {current_year}, must search for today news 
Your job:
1. Search for the latest crude oil news using the search tool
2. For each result, CHECK the publish date before saving:
   - ONLY save articles published on {current_date} or {yesterday}
   - If no publish date is visible on the article, SKIP it entirely
- If the article is older than {yesterday}, SKIP it
3. Save at least 2 items per run — if results are too old, search again with different keywords
4. Focus on: price movements, OPEC decisions, supply/demand, geopolitical impact on oil
 
After saving, provide a brief summary including the publish date of each article saved.""",
    )


def build_soros_agent() -> FunctionAgent:
    """Agent that searches for George Soros latest portfolio holdings."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    return FunctionAgent(
        tools=[search_tool, save_soros_tool],
        llm=llm,
        verbose=True,
        system_prompt=f"""You are a financial research agent tracking George Soros / Soros Fund Management portfolio.
Today is {current_date}, year is {current_year}.
 
Your job:
1. Search for the latest Soros Fund Management 13F filing or portfolio holdings
2. Find the top 10 holdings by portfolio weight
3. For each holding call save_soros_holding to persist it
4. You MUST correctly identify and set instrument_type for each position:
   - 'stock'   → regular shares/equity
   - 'etf'     → exchange traded fund (e.g. SPY, XOP, GLD)
   - 'put'     → PUT option — these are bearish or hedge positions, very important to flag
   - 'call'    → CALL option — bullish option positions
   - 'warrant' → warrants
   Put options are common in Soros portfolios as hedges — do NOT label them as stocks.
 
After saving, provide a summary table showing all 10 holdings with their instrument type clearly labelled.""",
    )


def build_daily_news_agent() -> FunctionAgent:
    """Agent that fetches global, London, and art news daily."""
    from datetime import timezone, timedelta
    try:
        from zoneinfo import ZoneInfo
        tz_london = ZoneInfo("Europe/London")
    except ImportError:
        import pytz
        tz_london = pytz.timezone("Europe/London")
    now_london = datetime.now(tz_london)
    today = now_london.strftime("%Y-%m-%d")
    yesterday = (now_london - timedelta(days=1)).strftime("%Y-%m-%d")
    tz_label = now_london.strftime("%Z")  # "GMT" or "BST"
 
    return FunctionAgent(
        tools=[search_tool, save_daily_news_tool],
        llm=llm,
        verbose=True,
        system_prompt=f"""You are a daily news curator.
Current date (London {tz_label}): {today}. Only save articles published on {today} or {yesterday}.
If an article has no visible publish date, skip it.
Skip any results from video platforms (YouTube, Vimeo, TikTok, Instagram, etc.) — text articles only.
 
Your job — find and save exactly these articles:
1. GLOBAL news — 2 most important global news stories today
   → category = 'global'
2. LONDON local news — 1 notable London local news story today
   → category = 'london'
3. ART news — 2 art-related news stories today (exhibitions, auctions, artists, museums)
   → category = 'art'
 
For each article call save_daily_news with the correct category, title, a 2-3 sentence summary, url, source name, and publish date.
After saving, provide a brief digest of all 5 articles grouped by category.""",
    )