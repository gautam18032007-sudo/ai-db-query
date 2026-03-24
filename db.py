"""
db.py – AlloyDB / PostgreSQL database layer.

Responsibilities:
  - Establish a connection pool to AlloyDB (PostgreSQL-compatible).
  - Seed a sample `products` dataset on first run (pgvector extension enabled
    so the table is ready for embedding-based similarity search).
  - Execute raw SQL returned by ai.py and return structured results.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, TABLE_NAME

# ---------------------------------------------------------------------------
# Connection pool (min 1, max 5 connections)
# ---------------------------------------------------------------------------
_pool: pool.SimpleConnectionPool | None = None


def get_pool() -> pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    return _pool


def get_conn():
    return get_pool().getconn()


def release_conn(conn):
    get_pool().putconn(conn)


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id          SERIAL PRIMARY KEY,
    name        TEXT        NOT NULL,
    category    TEXT        NOT NULL,
    price       NUMERIC(10, 2) NOT NULL,
    stock       INTEGER     NOT NULL DEFAULT 0,
    rating      NUMERIC(3, 1),
    description TEXT
);
"""

SEED_DATA = [
    ("Wireless Noise-Cancelling Headphones", "Electronics", 149.99, 35, 4.7,
     "Over-ear headphones with active noise cancellation and 30-hour battery life."),
    ("Ergonomic Office Chair", "Furniture", 329.00, 12, 4.5,
     "Lumbar-support mesh chair adjustable for all-day comfort."),
    ("Stainless Steel Water Bottle", "Kitchen", 24.95, 120, 4.8,
     "Double-walled 32 oz bottle keeps drinks cold 24 h or hot 12 h."),
    ("Mechanical Keyboard", "Electronics", 89.99, 60, 4.6,
     "Compact TKL layout with Cherry MX Brown switches and RGB backlight."),
    ("Yoga Mat Premium", "Sports", 45.00, 80, 4.4,
     "6mm thick non-slip mat with alignment lines; eco-friendly TPE foam."),
    ("Air Purifier HEPA", "Home Appliances", 199.00, 25, 4.3,
     "Covers up to 500 sq ft; removes 99.97 % of particles ≥ 0.3 microns."),
    ("Portable Bluetooth Speaker", "Electronics", 59.99, 45, 4.5,
     "IPX7 waterproof, 360° sound, 12-hour playback."),
    ("Cast Iron Skillet 12\"", "Kitchen", 39.95, 70, 4.9,
     "Pre-seasoned; compatible with all cooktops including induction."),
    ("Standing Desk Converter", "Furniture", 249.00, 18, 4.2,
     "Sit-stand desktop riser with smooth gas-spring lift mechanism."),
    ("Running Shoes Pro", "Sports", 119.99, 55, 4.6,
     "Lightweight breathable mesh upper with responsive foam midsole."),
    ("Smart LED Desk Lamp", "Electronics", 49.99, 90, 4.5,
     "Touch-control, 5 colour temperatures, USB-C charging port built in."),
    ("French Press Coffee Maker", "Kitchen", 34.99, 65, 4.7,
     "8-cup borosilicate glass carafe with stainless double-screen filter."),
    ("Foam Roller Deep Tissue", "Sports", 29.99, 100, 4.3,
     "High-density EVA foam; 36-inch length for full-back coverage."),
    ("Weighted Blanket 15lb", "Home", 79.00, 40, 4.6,
     "Glass-bead fill evenly distributed across 48×72\" premium cotton shell."),
    ("Noise Machine Sleep", "Home Appliances", 44.95, 55, 4.8,
     "30 soothing sounds, timer settings, compact bedside design."),
]


def init_db():
    """Create table and seed data if the table is empty."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Enable pgvector if available (AlloyDB ships with it)
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception:
                conn.rollback()  # ignore if unavailable

            cur.execute(CREATE_TABLE_SQL)
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
            count = cur.fetchone()[0]
            if count == 0:
                cur.executemany(
                    f"""
                    INSERT INTO {TABLE_NAME}
                        (name, category, price, stock, rating, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    SEED_DATA,
                )
        conn.commit()
    finally:
        release_conn(conn)


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

def execute_query(sql: str) -> dict:
    """
    Run a SQL SELECT statement and return:
      {
        "columns": [...],
        "rows":    [...],
        "count":   int,
        "error":   None | str
      }
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = list(rows[0].keys()) if rows else []
            return {
                "columns": columns,
                "rows": [dict(r) for r in rows],
                "count": len(rows),
                "error": None,
            }
    except Exception as exc:
        conn.rollback()
        return {"columns": [], "rows": [], "count": 0, "error": str(exc)}
    finally:
        release_conn(conn)


def get_schema() -> str:
    """Return a short human-readable schema description for the LLM prompt."""
    return (
        f"Table: {TABLE_NAME}\n"
        "Columns:\n"
        "  id          INTEGER  – primary key\n"
        "  name        TEXT     – product name\n"
        "  category    TEXT     – e.g. Electronics, Kitchen, Sports, Furniture, Home\n"
        "  price       NUMERIC  – price in USD\n"
        "  stock       INTEGER  – units available\n"
        "  rating      NUMERIC  – customer rating 0-5\n"
        "  description TEXT     – short product description\n"
    )