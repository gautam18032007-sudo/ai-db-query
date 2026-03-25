"""
app.py  –  Flask application

Routes:
  GET  /           → renders the query UI
  POST /execute    → receives { "sql": "SELECT ..." }, validates + runs it,
                     returns { columns, rows, count, error }
  GET  /schema     → returns { schema, system_prompt, summarise_prompt }
  GET  /all        → returns all rows (for initial table display)
  GET  /health     → liveness check

AI flow (all in the browser):
  1. User types a question.
  2. Frontend calls Anthropic API directly with the NL→SQL system prompt
     (no API key stored on the server).
  3. Frontend sends the returned SQL to POST /execute.
  4. Frontend calls Anthropic API again with the rows to get a summary.
"""

from flask import Flask, render_template, request, jsonify
from db import init_db, execute_query, get_schema, get_all_rows
from ai import validate_sql, get_nl2sql_system_prompt, get_summarise_system_prompt

app = Flask(__name__)
_db_ready = False


def ensure_db():
    global _db_ready
    if not _db_ready:
        try:
            init_db()
            _db_ready = True
        except Exception as exc:
            app.logger.warning(f"DB init failed (demo mode active): {exc}")
            _db_ready = True  # prevent retry storm


@app.before_request
def startup():
    ensure_db()


# ── Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/execute", methods=["POST"])
def execute():
    """Validate and run a SQL SELECT. Returns JSON results."""
    body = request.get_json(silent=True) or {}
    sql  = (body.get("sql") or "").strip()

    if not sql:
        return jsonify({"error": "No SQL provided."}), 400

    # Safety gate
    check = validate_sql(sql)
    if not check["ok"]:
        return jsonify({"error": f"SQL rejected: {check['reason']}"}), 422

    result = execute_query(sql)
    return jsonify(result)


@app.route("/schema")
def schema():
    """Return schema text + AI system prompts for the frontend."""
    return jsonify({
        "schema":           get_schema(),
        "system_prompt":    get_nl2sql_system_prompt(),
        "summarise_prompt": get_summarise_system_prompt(),
    })


@app.route("/all")
def all_rows():
    """Return all seeded rows for the initial browse view."""
    rows = get_all_rows()
    if not rows:
        return jsonify({"columns": [], "rows": [], "count": 0})
    return jsonify({"columns": list(rows[0].keys()), "rows": rows, "count": len(rows)})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "db_ready": _db_ready})


# ── Dev server ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)