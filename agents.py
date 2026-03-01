import os
from dotenv import load_dotenv
from datetime import datetime
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from tools import search_tool, save_crude_oil_tool, save_taiwan_law_tool

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
3. Save at least 3-5 items per run
4. Focus on: price movements, OPEC decisions, supply/demand, geopolitical impact on oil

After saving, provide a brief summary of what you found.""",
    )

