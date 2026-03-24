"""
ai.py – Natural-language → SQL translator powered by Claude (Anthropic API).

How it works:
  1. Receives the user's plain-English question plus the DB schema.
  2. Sends a structured prompt to Claude asking it to produce ONE safe
     SELECT statement and nothing else.
  3. Strips any markdown fences and returns the clean SQL string.
  4. A secondary `summarise_results` helper turns tabular data back into a
     human-readable sentence using Claude.
"""

import re
import anthropic
from config import ANTHROPIC_API_KEY, TABLE_NAME
from db import get_schema

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

NL2SQL_SYSTEM = """You are a precise PostgreSQL query generator.

Rules:
- Output ONLY a single SQL SELECT statement – no explanation, no markdown, no semicolons.
- The query must be read-only (SELECT only). Never use INSERT, UPDATE, DELETE, DROP, etc.
- Use only the table and columns described in the schema.
- Apply sensible LIMIT clauses (max 50 rows) unless the user explicitly asks for more.
- Use ILIKE for case-insensitive text matching.
- If the question is ambiguous, make the most helpful reasonable assumption.
- If the question cannot be answered with the given schema, output exactly: INVALID_QUERY
"""

SUMMARISE_SYSTEM = """You are a helpful data analyst assistant.
Given a natural-language question and JSON query results, write a concise 1-3 sentence
summary that directly answers the question. Be specific: include numbers, names, and
values from the data. If there are no results, say so clearly."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def natural_language_to_sql(question: str) -> dict:
    """
    Convert a natural-language question into a SQL SELECT statement.

    Returns:
        {
            "sql":   str | None,   # the generated SQL
            "error": str | None    # error message if generation failed
        }
    """
    schema = get_schema()
    user_prompt = (
        f"Schema:\n{schema}\n\n"
        f"Question: {question}\n\n"
        "Generate the SQL query:"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=NL2SQL_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:sql)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()

        if raw.upper().startswith("INVALID_QUERY"):
            return {
                "sql": None,
                "error": "Your question could not be mapped to the available data. "
                         "Try rephrasing or ask about products, prices, categories, stock, or ratings.",
            }

        # Basic safety guard: reject any non-SELECT statement
        first_token = raw.split()[0].upper() if raw.split() else ""
        if first_token != "SELECT":
            return {"sql": None, "error": "Generated query is not a SELECT statement."}

        return {"sql": raw, "error": None}

    except Exception as exc:
        return {"sql": None, "error": f"AI service error: {exc}"}


def summarise_results(question: str, results: dict) -> str:
    """
    Given the original question and query results dict, return a plain-English summary.
    Falls back gracefully if the API call fails.
    """
    if results.get("error"):
        return f"Query failed: {results['error']}"

    rows = results.get("rows", [])
    count = results.get("count", 0)

    if count == 0:
        return "No products matched your query."

    # Limit payload sent to Claude to avoid token bloat
    sample = rows[:10]
    user_prompt = (
        f"Question: {question}\n\n"
        f"Total rows returned: {count}\n"
        f"Data (first {len(sample)} rows):\n{sample}\n\n"
        "Provide a concise summary:"
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=256,
            system=SUMMARISE_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        return f"Found {count} result(s)."