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


def send_email(subject: str, body: str) -> bool:
    """Send a plain text email via Gmail SMTP."""
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    gmail_to = os.environ.get("GMAIL_TO")

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


def send_crude_oil_report(rows: list[dict] = None):
    """Fetch latest crude oil rows and email a summary."""
    if rows is None:
        rows = get_all_crude_oil()

    # Only email today's rows
    today = datetime.now().strftime("%Y-%m-%d")
    todays_rows = [r for r in rows if r["created_at"].startswith(today)]

    if not todays_rows:
        print("[EMAIL] No new rows today, skipping email.")
        return

    subject = f"Crude Oil News — {today} ({len(todays_rows)} articles)"
    body = build_crude_oil_summary(todays_rows)
    send_email(subject, body)