import re

def make_count_sql(sql: str) -> str:
    """
    Converts an LLM-produced SELECT into a SELECT COUNT(*),
    stripping ORDER BY and pagination (LIMIT/OFFSET/FETCH).
    """
    s = sql.strip().rstrip(";")

    # Remove LIMIT/OFFSET at the end
    s = re.sub(r"(?is)\s+limit\s+\S+(?:\s+offset\s+\S+)?" + r"(?:\s*;)?$", "", s)

    # Remove FETCH FIRST ... ROWS ONLY
    s = re.sub(r"(?is)\s+fetch\s+first\s+\S+\s+rows\s+only" + r"(?:\s*;)?$", "", s)

    # Remove OFFSET ... ROWS [FETCH NEXT ...]
    s = re.sub(r"(?is)\s+offset\s+\S+\s+rows(?:\s+fetch\s+next\s+\S+\s+rows\s+only)?" + r"(?:\s*;)?$", "", s)

    # Remove trailing ORDER BY
    s = re.sub(r"(?is)\s+order\s+by\s+[\s\S]*$", "", s)

    return f"SELECT COUNT(*) AS total_count FROM ({s}) AS sub"
