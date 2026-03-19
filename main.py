import asyncio
from dotenv import load_dotenv

load_dotenv()

from db import (
    init_db,
    init_soros_table,
    clear_soros_portfolio,
    get_existing_daily_news_urls
    # migrate_add_file_path,
    # get_existing_crude_oil_urls,
    # get_rows_without_file,
    # update_file_path,
)
from agents import build_crude_oil_agent, build_soros_agent, build_daily_news_agent
from emailer import send_daily_report, send_daily_news_global
# from emailer import send_daily_report


async def run_crude_oil_agent():
    print("\n" + "=" * 50)
    print("  CRUDE OIL AGENT")
    print("=" * 50)
    agent = build_crude_oil_agent()
    response = await agent.run(
        user_msg="Search for the latest crude oil news today, then save each relevant result to the database."
    )
    print("\n[CRUDE OIL SUMMARY]")
    print(response)



async def run_soros_agent():
    print("\n" + "=" * 50)
    print("  SOROS PORTFOLIO AGENT")
    print("=" * 50)
    # Always refresh — clear old data and fetch latest snapshot
    clear_soros_portfolio()
    agent = build_soros_agent()
    response = await agent.run(
        user_msg="Find the latest Soros Fund Management 13F portfolio holdings. Save the top 10 positions."
    )
    print("\n[SOROS SUMMARY]")
    print(response)


async def run_daily_news_agent():
    print("\n" + "=" * 50)
    print("  DAILY NEWS AGENT")
    print("=" * 50)
    existing_urls = get_existing_daily_news_urls()
    print(f"[DEDUP] {len(existing_urls)} existing URLs in DB.")
    agent = build_daily_news_agent()
    response = await agent.run(
        user_msg=f"""Find today's news digest: 2 global, 1 London, 2 art stories.
 
IMPORTANT - skip any article whose URL is already in this list:
{chr(10).join(f"- {u}" for u in existing_urls[-50:]) or "No existing URLs."}
 
Only save NEW articles."""
    )
    print("\n[DAILY NEWS SUMMARY]")
    print(response)



def format_url_list(urls: list[str]) -> str:
    if not urls:
        return "（目前資料庫為空，無需跳過任何網址）"
    recent = urls[-50:]
    return "\n".join(f"- {url}" for url in recent)


async def main():
    # 1. Init DB tables
    init_db()
    init_soros_table()


    # 2. Run agents 
    await run_crude_oil_agent()
    await run_soros_agent()
    # await run_daily_news_agent()

    # 3. Email today's crude oil results
    print("\n" + "=" * 50)
    print("  SENDING EMAIL REPORT")
    print("=" * 50)

    # 4. Email today's news digest
    send_daily_report()
    # send_daily_news_global()


    print("\n" + "=" * 50)
    print("  FINISH TASK")
    print("=" * 50)



if __name__ == "__main__":
    asyncio.run(main())