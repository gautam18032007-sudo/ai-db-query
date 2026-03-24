def is_safe_query(sql: str) -> bool:
    """
    Check if the SQL query is safe (read-only SELECT statement).
    """
    sql = sql.strip().upper()
    return sql.startswith('SELECT') and not any(keyword in sql for keyword in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'])