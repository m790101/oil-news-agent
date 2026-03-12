import os
from dotenv import load_dotenv
from datetime import datetime
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from tools import search_tool, save_crude_oil_tool, save_taiwan_law_tool, save_soros_tool

load_dotenv()

llm = OpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY", ""))


def build_crude_oil_agent() -> FunctionAgent:
    """Agent that searches for crude oil news and saves results to DB."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    return FunctionAgent(
        tools=[search_tool, save_crude_oil_tool],
        llm=llm,
        verbose=True,
        system_prompt=f"""You are a crude oil market research agent.
        today is {current_date}, year is {current_year}, must search for today news 

Your job:
1. Search for the latest crude oil news using the search tool
2. For each relevant result, call save_crude_oil_news to persist it
3. Save at least 2-4 items per run
4. Focus on: price movements, OPEC decisions, supply/demand, geopolitical impact on oil

After saving, provide a brief summary of what you found.""",
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