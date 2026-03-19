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


def send_email(subject: str, body: str, to: str, html: bool = False) -> bool:
    """Send a plain text email via Gmail SMTP."""
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not all([gmail_user, gmail_password, to]):
        print("[EMAIL] Missing Gmail credentials in .env — skipping.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = gmail_user
    msg["To"] = to
    msg["Subject"] = subject
    mime_type = "html" if html else "plain"
    msg.attach(MIMEText(body, mime_type, "utf-8"))
    # msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to, msg.as_bytes())
            # server.sendmail(gmail_user, to, msg.as_string())
        print(f"[EMAIL] Sent to {to}")
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
    """Format daily news rows into plain text grouped by category."""
    if not rows:
        return "No daily news found."
 
    category_labels = {
        "global": "🌍 GLOBAL NEWS",
        "london": "🇬🇧 LONDON NEWS",
        "art":    "🎨 ART NEWS",
    }
 
    # Group by category
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

def generate_news_brief(rows: list[dict]) -> str:
    """Use LLM to generate a 2-3 sentence brief summarising the day's news."""
    try:
        from llama_index.llms.openai import OpenAI as LlamaOpenAI
        titles = "\n".join(f"- [{r['category'].upper()}] {r['title']}" for r in rows if r.get("category") in ("global", "london"))
        llm = LlamaOpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY", ""))
        response = llm.complete(
            f"Based on these news headlines, write a friendly 1-3 sentence briefing, less than 50 words "
            f"that captures the overall mood and most notable story of the day. "
            f"Keep it conversational, not robotic.\n\n{titles}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"[EMAIL] Could not generate brief: {e}")
        return "Here is your daily news digest."
 
def build_daily_news_html(rows: list[dict]) -> str:
    """Format daily news as HTML email with LLM-generated brief at the top."""
    if not rows:
        return "<p>No daily news found.</p>"
 
    today = datetime.now().strftime("%B %d, %Y")
    brief = generate_news_brief(rows)
 
    category_config = {
        "global": {"label": "🌍 Global News",  "color": "#2c3e50"},
        "london": {"label": "🇬🇧 London News", "color": "#1a5276"},
        "art":    {"label": "🎨 Art News",      "color": "#6c3483"},
    }
    grouped = {"global": [], "london": [], "art": []}
    for row in rows:
        cat = row.get("category", "global")
        if cat in grouped:
            grouped[cat].append(row)
    sections_html = ""
    for cat, cfg in category_config.items():
        items = grouped.get(cat, [])
        if not items:
            continue
        articles_html = ""
        for row in items:
            articles_html += (
                f'<div style="border-left:3px solid {cfg["color"]};padding:10px 15px;'
                f'margin-bottom:16px;background:#fafafa;">'
                f'<div style="font-size:16px;font-weight:600;color:#1a1a1a;margin-bottom:6px;">'
                f'<a href="{row["url"]}" style="color:#1a1a1a;text-decoration:none;">{row["title"]}</a></div>'
                f'<div style="font-size:14px;color:#444;line-height:1.6;margin-bottom:6px;">{row["summary"]}</div>'
                f'<div style="font-size:12px;color:#888;">{row["source"]} &bull; {row["published_date"]}</div>'
                f'</div>'
            )
        sections_html += (
            f'<div style="margin-bottom:32px;">'
            f'<div style="background:{cfg["color"]};color:white;padding:10px 16px;'
            f'border-radius:4px 4px 0 0;font-size:15px;font-weight:700;">{cfg["label"]}</div>'
            f'<div style="border:1px solid #e0e0e0;border-top:none;padding:16px;'
            f'border-radius:0 0 4px 4px;">{articles_html}</div>'
            f'</div>'
        )
 
    return (
        '<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f4f4f4;'
        'font-family:Arial,sans-serif;">'
        '<div style="max-width:620px;margin:30px auto;background:white;border-radius:8px;'
        'box-shadow:0 2px 8px rgba(0,0,0,0.08);overflow:hidden;">'
        '<div style="background:#1a1a2e;padding:24px 28px;">'
        '<div style="color:white;font-size:22px;font-weight:700;">Daily News Digest</div>'
        f'<div style="color:#aaa;font-size:13px;margin-top:4px;">{today}</div>'
        '</div>'
        '<div style="background:#eef2f7;padding:18px 28px;border-bottom:1px solid #dde3ec;">'
        f'<div style="font-size:14px;color:#2c3e50;line-height:1.7;font-style:italic;">{brief}</div>'
        '</div>'
        f'<div style="padding:24px 28px;">{sections_html}</div>'
        '<div style="background:#f8f8f8;border-top:1px solid #eee;padding:14px 28px;'
        'font-size:11px;color:#aaa;text-align:center;">Sent by your Daily News Agent</div>'
        '</div></body></html>'
    )


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
    """Send daily news digest only to external recipient."""
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
 
    subject = f"Daily News Digest — {today}"
    body = build_daily_news_html(news_rows)
    send_email(subject, body, to=recipient, html=True) 