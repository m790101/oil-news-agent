import asyncio
from dotenv import load_dotenv

load_dotenv()

from db import (
    init_db,
    init_soros_table,
    clear_soros_portfolio
    # migrate_add_file_path,
    # get_existing_crude_oil_urls,
    # get_rows_without_file,
    # update_file_path,
)
from agents import build_crude_oil_agent, build_soros_agent
from emailer import send_daily_report


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




def format_url_list(urls: list[str]) -> str:
    if not urls:
        return "（目前資料庫為空，無需跳過任何網址）"
    recent = urls[-50:]
    return "\n".join(f"- {url}" for url in recent)


async def main():
    # 1. Init DB tables
    init_db()
    init_soros_table()


    # 2. Run crude oil agent
    await run_crude_oil_agent()
    await run_soros_agent()

    # 3. Email today's crude oil results
    print("\n" + "=" * 50)
    print("  SENDING EMAIL REPORT")
    print("=" * 50)
    send_daily_report()


    print("\n" + "=" * 50)
    print("  FINISH TASK")
    print("=" * 50)



if __name__ == "__main__":
    asyncio.run(main())