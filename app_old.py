"""
app.py — Flask REST API + UI server

Routes:
  GET  /                → main UI
  GET  /api/health      → liveness + DB/AI status check
  GET  /api/stats       → dashboard statistics
  GET  /api/schema      → table schema text
  GET  /api/browse      → all rows (for Browse tab)
  POST /api/query       → full NL→SQL→execute→summarise pipeline
  POST /api/execute     → run a raw SQL string (validated)
  POST /api/chat        → AI chatbot (multi-turn)
"""

import logging
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from config import SECRET_KEY, DEBUG, ANTHROPIC_API_KEY
from db import init_db, execute_query, get_table_stats, get_all_rows, get_schema_text, TABLE_NAME
from ai import nl_to_sql, summarise, chat, validate_sql

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)

_db_ok  = False
_ai_ok  = False


@app.before_request
def startup():
    """One-time init on first request."""
    global _db_ok, _ai_ok
    if not getattr(app, "_started", False):
        app._started = True

        _db_ok = init_db()
        _ai_ok = bool(ANTHROPIC_API_KEY)

        if _db_ok:
            log.info("AlloyDB ready")
        else:
            log.warning("AlloyDB unavailable — running in demo mode")

        if _ai_ok:
            log.info("Anthropic API key present")
        else:
            log.warning("ANTHROPIC_API_KEY not set — AI features disabled")


# ── Helper ─────────────────────────────────────────────────────────────────

def err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ── UI ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", ai_enabled=_ai_ok, db_enabled=_db_ok)


# ── API ────────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({
        "status":     "ok",
        "db_ready":   _db_ok,
        "ai_ready":   _ai_ok,
        "table":      TABLE_NAME,
    })


@app.route("/api/stats")
def stats():
    data = get_table_stats()
    return jsonify(data)


@app.route("/api/schema")
def schema():
    return jsonify({"schema": get_schema_text()})


@app.route("/api/browse")
def browse():
    result = get_all_rows()
    return jsonify(result)


@app.route("/api/query", methods=["POST"])
def query():
    """
    Full pipeline: natural language → SQL → execute → AI summary.
    Body: { "question": "show me electronics under $100" }
    """
    body     = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()

    if not question:
        return err("Question is required.")

    if not _ai_ok:
        return err("AI is not configured. Add ANTHROPIC_API_KEY to your .env file.", 503)

    # Step 1 – NL → SQL
    nl_result = nl_to_sql(question)
    if nl_result["error"]:
        return jsonify({"error": nl_result["error"], "step": "nl_to_sql"}), 422

    sql = nl_result["sql"]

    # Step 2 – Execute on AlloyDB
    if not _db_ok:
        return jsonify({
            "sql":     sql,
            "columns": [],
            "rows":    [],
            "count":   0,
            "summary": "Database is not connected. The SQL was generated but could not be executed.",
            "error":   "Database unavailable",
        })

    db_result = execute_query(sql)

    # Step 3 – Summarise
    summary = summarise(question, db_result["rows"], db_result["count"])

    return jsonify({
        "sql":     sql,
        "columns": db_result["columns"],
        "rows":    db_result["rows"],
        "count":   db_result["count"],
        "summary": summary,
        "error":   db_result.get("error"),
    })


@app.route("/api/execute", methods=["POST"])
def execute():
    """
    Execute a raw SQL string (must be SELECT).
    Body: { "sql": "SELECT ..." }
    """
    body = request.get_json(silent=True) or {}
    sql  = (body.get("sql") or "").strip()

    if not sql:
        return err("SQL is required.")

    check = validate_sql(sql)
    if not check["ok"]:
        return err(f"SQL rejected: {check['reason']}", 422)

    result = execute_query(sql)
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def chatbot():
    """
    Multi-turn AI chatbot.
    Body: { "messages": [{"role":"user","content":"..."}, ...] }
    """
    body     = request.get_json(silent=True) or {}
    messages = body.get("messages") or []

    if not messages:
        return err("messages array is required.")

    if not _ai_ok:
        return jsonify({"reply": "AI is not configured. Please add your ANTHROPIC_API_KEY to the .env file."})

    reply = chat(messages)
    return jsonify({"reply": reply})


# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)