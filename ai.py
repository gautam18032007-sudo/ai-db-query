"""
ai.py  –  Server-side AI helpers (lightweight)

The heavy AI work (NL→SQL generation, result summarisation) is now done
client-side in the browser, which calls the Anthropic API directly.
This module only provides:
  - validate_sql()  : safety-check a SQL string before execution
  - schema_prompt() : return the system prompt text the frontend should use
"""

import re
from db import get_schema

# Allowed SQL: SELECT only, no dangerous keywords
_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|EXEC|EXECUTE|"
    r"COPY|VACUUM|ANALYSE|ANALYZE|REINDEX|CLUSTER|COMMENT|LOCK|CALL)\b",
    re.IGNORECASE,
)


def validate_sql(sql: str) -> dict:
    """
    Return {"ok": True} or {"ok": False, "reason": "..."}.
    Checks:
      1. First token must be SELECT.
      2. No dangerous mutation/DDL keywords anywhere.
      3. No semicolons (prevents stacked queries).
    """
    stripped = sql.strip()

    if not stripped:
        return {"ok": False, "reason": "Empty SQL string."}

    first = stripped.split()[0].upper()
    if first != "SELECT":
        return {"ok": False, "reason": f"Only SELECT statements are allowed (got {first})."}

    if _BLOCKED.search(stripped):
        kw = _BLOCKED.search(stripped).group()
        return {"ok": False, "reason": f"Forbidden keyword in query: {kw}"}

    if ";" in stripped:
        return {"ok": False, "reason": "Semicolons are not allowed (prevents query stacking)."}

    return {"ok": True, "reason": None}


def get_nl2sql_system_prompt() -> str:
    """Return the system prompt the frontend passes to the Anthropic API."""
    schema = get_schema()
    return (
        "You are a precise PostgreSQL query generator for a product database.\n\n"
        f"DATABASE SCHEMA:\n{schema}\n\n"
        "RULES — follow exactly:\n"
        "1. Output ONLY a single SQL SELECT statement. No explanation, no markdown, "
        "no code fences, no semicolons.\n"
        "2. The query must be read-only (SELECT only).\n"
        "3. Use only the columns listed in the schema above.\n"
        "4. Apply LIMIT 50 unless the user asks for more.\n"
        "5. Use ILIKE for case-insensitive text search.\n"
        "6. If the question cannot be answered with the schema, output exactly: "
        "CANNOT_ANSWER\n"
        "7. Do NOT include ```sql or ``` in your response.\n"
        "8. Output the raw SQL and nothing else."
    )


def get_summarise_system_prompt() -> str:
    """Return the system prompt for result summarisation."""
    return (
        "You are a helpful data analyst. Given a natural-language question and "
        "structured query results, write a clear 2-3 sentence summary that directly "
        "answers the question. Include specific numbers, names, and values from the "
        "data. If there are no results, say so clearly and suggest a rephrasing."
    )