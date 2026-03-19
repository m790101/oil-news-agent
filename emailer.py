import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from db import get_all_crude_oil

load_dotenv()


def build_crude_oil_summary(rows: list[dict]) -> str:
    """Format crude oil DB rows into a plain text email body."""
    if not rows:
        return "No crude oil news was saved in this run."

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"Crude Oil News Summary — {today}",
        f"{'=' * 50}",
        f"Total articles: {len(rows)}",
        "",
    ]

    for i, row in enumerate(rows, start=1):
        lines.append(f"{i}. {row['title']}")
        lines.append(f"   Source : {row['source']}")
        lines.append(f"   URL    : {row['url']}")
        lines.append(f"   Summary: {row['summary']}")
        lines.append(f"   Saved  : {row['created_at']}")
        lines.append("")

    return "\n".join(lines)


def send_email(subject: str, body: str, to: str) -> bool:
    """Send a plain text email via Gmail SMTP."""
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    # gmail_to = os.environ.get("GMAIL_TO")
    gmail_to = to 

    if not all([gmail_user, gmail_password, gmail_to]):
        print("[EMAIL] Missing Gmail credentials in .env — skipping.")
        return False

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, gmail_to, msg.as_string())
        print(f"[EMAIL] Sent to {gmail_to}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False



def build_soros_summary(rows: list[dict]) -> str:
    """Format Soros portfolio rows into plain text with instrument type clearly shown."""
    if not rows:
        return "No Soros portfolio data found."
 
    # Label map with emoji for quick visual scanning
    type_labels = {
        "stock":   "📈 STOCK  ",
        "etf":     "🗂  ETF    ",
        "put":     "🔴 PUT    ",
        "call":    "🟢 CALL   ",
        "warrant": "📜 WARRANT",
    }
 
    lines = [
        "George Soros / Soros Fund Management — Top 10 Holdings (Latest 13F)",
        "=" * 70,
        f"{'#':<4} {'Type':<12} {'Ticker':<8} {'Company':<32} {'Value':>8}  {'Wt%':>6}  Change",
        "-" * 70,
    ]
 
    for row in rows:
        itype = (row.get("instrument_type") or "stock").lower()
        label = type_labels.get(itype, f"  {itype.upper():<8}")
        lines.append(
            f"#{row['rank']:<3} {label}  {row['ticker']:<8} {row['company']:<32} "
            f"{row['value_usd']:>8}  {row['portfolio_pct']:>6}  {row['change_note']}"
        )
 
    lines.append("-" * 70)
    lines.append(f"Source: {rows[0].get('source', 'N/A')}")
    lines.append(f"* 🔴 PUT positions are hedges/bearish bets, not direct ownership")
    return "\n".join(lines)



 
def build_daily_news_summary(rows: list[dict]) -> str:
    if not rows:
        return "No daily news found."
    category_labels = {
        "global": "GLOBAL NEWS",
        "london": "LONDON NEWS",
        "art":    "ART NEWS",
    }
    grouped = {"global": [], "london": [], "art": []}
    for row in rows:
        cat = row.get("category", "global")
        if cat in grouped:
            grouped[cat].append(row)
    lines = ["Daily News Digest", "=" * 50, ""]
    for cat, label in category_labels.items():
        items = grouped.get(cat, [])
        if not items:
            continue
        lines.append(label)
        lines.append("-" * 40)
        for i, row in enumerate(items, 1):
            lines.append(f"{i}. {row['title']}")
            lines.append(f"   {row['summary']}")
            lines.append(f"   Source: {row['source']} | {row['published_date']} | {row['url']}")
            lines.append("")
    return "\n".join(lines)


def send_daily_report(crude_oil_rows: list[dict] = None, soros_rows: list[dict] = None):
    """Send a combined daily report with crude oil news and Soros portfolio."""
    from db import get_all_crude_oil, get_soros_portfolio
    today = datetime.now().strftime("%Y-%m-%d")
 
    # ---- Crude Oil ----
    if crude_oil_rows is None:
        all_rows = get_all_crude_oil()
        crude_oil_rows = [r for r in all_rows if r["created_at"].startswith(today)]
 
    # ---- Soros Portfolio ----
    if soros_rows is None:
        soros_rows = get_soros_portfolio()
 
    if not crude_oil_rows and not soros_rows:
        print("[EMAIL] Nothing to send today.")
        return
 
    subject = f"Daily Market Report — {today}"
    body = "\n\n".join(filter(None, [
        build_crude_oil_summary(crude_oil_rows),
        build_soros_summary(soros_rows),
    ]))
 
    send_email(subject, body, to=os.environ.get("GMAIL_TO"))
 



def send_daily_news_global(news_rows: list[dict] = None):
    from db import get_daily_news_by_date
    today = datetime.now().strftime("%Y-%m-%d")
    if news_rows is None:
        news_rows = get_daily_news_by_date(today)
    if not news_rows:
        print("[EMAIL] No news to send to external recipient.")
        return
    recipient = os.environ.get("GMAIL_EMILY")
    if not recipient:
        print("[EMAIL] GMAIL_EMILY not set in .env — skipping external email.")
        return
    subject = f"Daily News Digest - {today}"
    body = build_daily_news_summary(news_rows)
    send_email(subject, body, to=recipient)