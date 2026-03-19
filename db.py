import sqlite3
from datetime import datetime

DB_PATH = "data.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crude_oil_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            summary TEXT,
            url TEXT UNIQUE,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taiwan_futures_law (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            url TEXT UNIQUE,
            source TEXT,
            category TEXT,
            relevance_score REAL,
            is_vectorized INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,   -- 'global', 'london', 'art'
            title TEXT,
            summary TEXT,
            url TEXT UNIQUE,
            source TEXT,
            published_date TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialized.")


def insert_crude_oil(title: str, summary: str, url: str, source: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO crude_oil_news (title, summary, url, source) VALUES (?, ?, ?, ?)",
            (title, summary, url, source),
        )
        conn.commit()
        print(f"[DB] Saved crude oil: {title[:60]}")
    except Exception as e:
        print(f"[DB] Error inserting crude oil: {e}")
    finally:
        conn.close()


def insert_taiwan_law(
    title: str, content: str, url: str, source: str, category: str, relevance_score: float
):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO taiwan_futures_law
               (title, content, url, source, category, relevance_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, content, url, source, category, relevance_score),
        )
        conn.commit()
        print(f"[DB] Saved Taiwan law: {title[:60]} | {category} | score={relevance_score}")
    except Exception as e:
        print(f"[DB] Error inserting Taiwan law: {e}")
    finally:
        conn.close()


# ── Duplicate-check helpers ─────────────────────────────────────────────────

def get_existing_crude_oil_urls() -> list[str]:
    """Return all URLs already saved in crude_oil_news."""
    conn = get_connection()
    rows = conn.execute("SELECT url FROM crude_oil_news").fetchall()
    conn.close()
    return [row["url"] for row in rows]


def get_existing_taiwan_law_urls() -> list[str]:
    """Return all URLs already saved in taiwan_futures_law."""
    conn = get_connection()
    rows = conn.execute("SELECT url FROM taiwan_futures_law").fetchall()
    conn.close()
    return [row["url"] for row in rows]


# ── Other queries ───────────────────────────────────────────────────────────

def get_unvectorized_taiwan_law():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM taiwan_futures_law WHERE is_vectorized = 0"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_as_vectorized(row_id: int):
    conn = get_connection()
    conn.execute("UPDATE taiwan_futures_law SET is_vectorized = 1 WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()


def get_all_crude_oil():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM crude_oil_news ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_taiwan_law_by_category(category: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM taiwan_futures_law WHERE category = ? ORDER BY relevance_score DESC",
        (category,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def migrate_add_file_path():
    """Add file_path column to both tables if not already present."""
    conn = get_connection()
    for table in ["crude_oil_news", "taiwan_futures_law"]:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN file_path TEXT")
            print(f"[DB] Added file_path column to {table}")
        except Exception:
            pass  # Column already exists
    conn.commit()
    conn.close()


def update_file_path(table: str, url: str, file_path: str):
    """Store the local scraped file path for a given URL."""
    conn = get_connection()
    conn.execute(
        f"UPDATE {table} SET file_path = ? WHERE url = ?",
        (file_path, url),
    )
    conn.commit()
    conn.close()


def get_rows_without_file(table: str) -> list[dict]:
    """Return rows that have a URL but no scraped file yet."""
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE file_path IS NULL AND url IS NOT NULL"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Soros Portfolio ─────────────────────────────────────────────────────────


def init_soros_table():
    """Create soros_portfolio table if not exists."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS soros_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            ticker TEXT,
            company TEXT,
            sector TEXT,
            instrument_type TEXT DEFAULT 'stock',  -- 'stock', 'etf', 'put', 'call', 'warrant'
            value_usd TEXT,
            portfolio_pct TEXT,
            change_note TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    # Migrate existing DB if column missing
    try:
        conn.execute("ALTER TABLE soros_portfolio ADD COLUMN instrument_type TEXT DEFAULT 'stock'")
    except Exception:
        pass
    conn.commit()
    conn.close()

 
 
def clear_soros_portfolio():
    """Clear old portfolio data before inserting fresh snapshot."""
    conn = get_connection()
    conn.execute("DELETE FROM soros_portfolio")
    conn.commit()
    conn.close()
    print("[DB] Cleared old Soros portfolio data.")
 
 
def insert_soros_holding(
    rank: int, ticker: str, company: str, sector: str,
    instrument_type: str, value_usd: str, portfolio_pct: str,
    change_note: str, source: str
):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO soros_portfolio
               (rank, ticker, company, sector, instrument_type, value_usd, portfolio_pct, change_note, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (rank, ticker, company, sector, instrument_type, value_usd, portfolio_pct, change_note, source),
        )
        conn.commit()
        print(f"[DB] Saved Soros holding #{rank}: [{instrument_type.upper()}] {ticker} - {company}")
    except Exception as e:
        print(f"[DB] Error inserting Soros holding: {e}")
    finally:
        conn.close()
 
 
def get_soros_portfolio():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM soros_portfolio ORDER BY rank ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]




def insert_daily_news(category: str, title: str, summary: str, url: str, source: str, published_date: str):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO daily_news (category, title, summary, url, source, published_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (category, title, summary, url, source, published_date),
        )
        conn.commit()
        print(f"[DB] Saved daily news [{category}]: {title[:60]}")
    except Exception as e:
        print(f"[DB] Error inserting daily news: {e}")
    finally:
        conn.close()
 
 
def get_existing_daily_news_urls() -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT url FROM daily_news").fetchall()
    conn.close()
    return [row["url"] for row in rows]
 
 
def get_daily_news_by_date(date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM daily_news WHERE created_at LIKE ? ORDER BY category, id",
        (f"{date}%",),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]