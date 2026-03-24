"""
app.py – Flask web application entry point.

Routes:
  GET  /          → renders the query UI (templates/index.html)
  POST /query     → accepts JSON { "question": "..." }
                    returns JSON with sql, results, summary, or error
  GET  /schema    → returns the table schema for display in the UI
  GET  /health    → simple liveness check
"""

from flask import Flask, render_template, request, jsonify
from db import init_db, execute_query, get_schema
from ai import natural_language_to_sql, summarise_results

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Initialise DB on startup
# ---------------------------------------------------------------------------
@app.before_request
def _startup():
    """Lazy one-time initialisation: create table + seed data."""
    if not getattr(app, "_db_initialised", False):
        try:
            init_db()
            app._db_initialised = True
        except Exception as exc:
            app.logger.warning(f"DB init skipped (demo mode): {exc}")
            app._db_initialised = True  # don't retry on every request


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/query", methods=["POST"])
def query():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    # Step 1: natural language → SQL
    nl_result = natural_language_to_sql(question)
    if nl_result["error"]:
        return jsonify({"error": nl_result["error"]}), 422

    sql = nl_result["sql"]

    # Step 2: execute SQL against AlloyDB
    db_result = execute_query(sql)

    # Step 3: summarise results in plain English
    summary = summarise_results(question, db_result)

    return jsonify({
        "sql":     sql,
        "columns": db_result["columns"],
        "rows":    db_result["rows"],
        "count":   db_result["count"],
        "summary": summary,
        "error":   db_result.get("error"),
    })


@app.route("/schema")
def schema():
    return jsonify({"schema": get_schema()})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Dev server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)