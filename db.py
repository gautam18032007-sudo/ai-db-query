"""
db.py  –  AlloyDB / PostgreSQL database layer

Responsibilities:
  - Manage a psycopg2 connection pool to AlloyDB.
  - Seed a sample `products` dataset on first run.
  - Execute SELECT statements and return structured JSON-serialisable results.
  - Expose the table schema as a plain-text string for the AI prompt.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool as pg_pool
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, TABLE_NAME

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pg_pool.SimpleConnectionPool(
            minconn=1, maxconn=5,
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        )
    return _pool


def get_conn():
    return get_pool().getconn()


def release_conn(conn):
    get_pool().putconn(conn)


# ── Schema & seed data ────────────────────────────────────────────────────

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id          SERIAL PRIMARY KEY,
    name        TEXT           NOT NULL,
    category    TEXT           NOT NULL,
    price       NUMERIC(10,2)  NOT NULL,
    stock       INTEGER        NOT NULL DEFAULT 0,
    rating      NUMERIC(3,1),
    description TEXT
);
"""

SEED_DATA = [
    ("Wireless Noise-Cancelling Headphones", "Electronics", 149.99, 35, 4.7,
     "Over-ear headphones with active noise cancellation and 30-hour battery life."),
    ("Ergonomic Office Chair",               "Furniture",   329.00, 12, 4.5,
     "Lumbar-support mesh chair adjustable for all-day comfort."),
    ("Stainless Steel Water Bottle",         "Kitchen",      24.95, 120, 4.8,
     "Double-walled 32 oz bottle keeps drinks cold 24 h or hot 12 h."),
    ("Mechanical Keyboard",                  "Electronics",  89.99,  60, 4.6,
     "Compact TKL layout with Cherry MX Brown switches and RGB backlight."),
    ("Yoga Mat Premium",                     "Sports",       45.00,  80, 4.4,
     "6mm thick non-slip mat with alignment lines; eco-friendly TPE foam."),
    ("Air Purifier HEPA",                    "Home",        199.00,  25, 4.3,
     "Covers up to 500 sq ft; removes 99.97% of particles >= 0.3 microns."),
    ("Portable Bluetooth Speaker",           "Electronics",  59.99,  45, 4.5,
     "IPX7 waterproof, 360 sound, 12-hour playback."),
    ('Cast Iron Skillet 12"',                "Kitchen",      39.95,  70, 4.9,
     "Pre-seasoned; compatible with all cooktops including induction."),
    ("Standing Desk Converter",              "Furniture",   249.00,  18, 4.2,
     "Sit-stand desktop riser with smooth gas-spring lift mechanism."),
    ("Running Shoes Pro",                    "Sports",      119.99,  55, 4.6,
     "Lightweight breathable mesh upper with responsive foam midsole."),
    ("Smart LED Desk Lamp",                  "Electronics",  49.99,  90, 4.5,
     "Touch-control, 5 colour temperatures, USB-C charging port built in."),
    ("French Press Coffee Maker",            "Kitchen",      34.99,  65, 4.7,
     "8-cup borosilicate glass carafe with stainless double-screen filter."),
    ("Foam Roller Deep Tissue",              "Sports",       29.99, 100, 4.3,
     "High-density EVA foam; 36-inch length for full-back coverage."),
    ("Weighted Blanket 15lb",                "Home",         79.00,  40, 4.6,
     "Glass-bead fill evenly distributed across 48x72 premium cotton shell."),
    ("Noise Machine Sleep",                  "Home",         44.95,  55, 4.8,
     "30 soothing sounds, timer settings, compact bedside design."),
    ("4K Webcam Pro",                        "Electronics",  99.99,  30, 4.4,
     "1080p/4K autofocus webcam with built-in ring light and noise-cancelling mic."),
    ("Bamboo Cutting Board Set",             "Kitchen",      32.00,  85, 4.6,
     "3-piece set with juice groove; naturally antimicrobial bamboo."),
    ("Resistance Bands Set",                 "Sports",       19.99, 150, 4.5,
     "5 resistance levels, latex-free, includes carry bag."),
    ("Electric Kettle 1.7L",                 "Kitchen",      44.99,  60, 4.7,
     "1500W rapid boil, 6 temperature presets, keep-warm function."),
    ("Monitor Light Bar",                    "Electronics",  35.99,  75, 4.5,
     "Clip-on LED bar with auto-dimming sensor and USB-C power."),
]


def init_db():
    """Create table and seed data if empty. Called once on app startup."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # pgvector is available on AlloyDB; ignore if not present locally
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
            except Exception:
                conn.rollback()

            cur.execute(CREATE_TABLE_SQL)
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    f"INSERT INTO {TABLE_NAME} "
                    "(name, category, price, stock, rating, description) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    SEED_DATA,
                )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise exc
    finally:
        release_conn(conn)


# ── Query execution ───────────────────────────────────────────────────────

def execute_query(sql: str) -> dict:
    """
    Run a SQL SELECT and return:
      { columns, rows, count, error }
    All values are JSON-serialisable (Decimal → float).
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            raw_rows = cur.fetchall()
            rows = []
            for r in raw_rows:
                row = {}
                for k, v in r.items():
                    # Convert Decimal to float for JSON
                    try:
                        from decimal import Decimal
                        row[k] = float(v) if isinstance(v, Decimal) else v
                    except Exception:
                        row[k] = str(v)
                rows.append(row)
            columns = list(rows[0].keys()) if rows else []
            return {"columns": columns, "rows": rows, "count": len(rows), "error": None}
    except Exception as exc:
        conn.rollback()
        return {"columns": [], "rows": [], "count": 0, "error": str(exc)}
    finally:
        release_conn(conn)


def get_schema() -> str:
    """Return human-readable schema for display and AI prompts."""
    return (
        f"Table: {TABLE_NAME}\n"
        "Columns:\n"
        "  id          INTEGER  – primary key, auto-increment\n"
        "  name        TEXT     – product name\n"
        "  category    TEXT     – one of: Electronics, Kitchen, Sports, Furniture, Home\n"
        "  price       NUMERIC  – price in USD (e.g. 49.99)\n"
        "  stock       INTEGER  – units currently in stock\n"
        "  rating      NUMERIC  – customer rating 0.0 to 5.0\n"
        "  description TEXT     – short product description\n"
        "\n"
        "Sample categories: Electronics, Kitchen, Sports, Furniture, Home\n"
        "Total rows: ~20 sample products\n"
    )


def get_all_rows() -> list:
    """Return all rows for demo / fallback display."""
    result = execute_query(f"SELECT * FROM {TABLE_NAME} ORDER BY id LIMIT 20;")
    return result.get("rows", [])