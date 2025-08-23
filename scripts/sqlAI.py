import os
import re
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Config ----------
DB_PATH = Path("data/recipes.db")  # adjust if your path differs
MAX_ROWS = 50                      # default limit for display
# ----------------------------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- LLM: NL -> SQL ----------
def nl_to_sql(query: str) -> str:
    """
    Convert a natural-language question to a single SQLite SELECT statement
    against the `recipes` table.
    """
    system = (
        "You convert natural-language questions to ONE SQLite SQL SELECT statement. "
        "Return ONLY the SQL text. No markdown fences, no explanation. "
        "Use the exact column names from this schema and add a LIMIT if the user does not specify one.\n\n"
        "Table: recipes(\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  title TEXT NOT NULL,\n"
        "  cook_time INTEGER,\n"
        "  prep_time INTEGER,\n"
        "  ratings REAL,\n"
        "  cuisine TEXT,\n"
        "  category TEXT,\n"
        "  author TEXT,\n"
        "  image TEXT,\n"
        "  ingredients_json TEXT NOT NULL\n"
        ")"
    )
    user = (
        f"Question: {query}\n"
        f"If filtering text columns (title, cuisine, category, author), you may use COLLATE NOCASE.\n"
        f"If no LIMIT is present, append 'LIMIT {MAX_ROWS}'.\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()

# ---------- Safety: clean SQL ----------
def clean_sql(text: str) -> str:
    t = text.strip()
    m = re.search(r"```(?:sql)?\s*(.*?)\s*```", t, flags=re.S | re.I)
    if m:
        t = m.group(1).strip()
    t = t.replace("`", "").strip()
    # keep only first statement
    if ";" in t:
        t = t.split(";", 1)[0].strip() + ";"
    if not t.upper().startswith("SELECT"):
        raise ValueError(f"Refusing to execute non-SELECT SQL: {t}")
    return t

# ---------- DB helpers ----------
def run_sql(sql: str):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall()
        return cols, rows
    finally:
        conn.close()

def pretty_print(cols, rows, max_rows: int = 25):
    if not rows:
        print("(no results)")
        return

    # Expand ingredients_json for readability if present
    if "ingredients_json" in cols:
        idx = cols.index("ingredients_json")
        expanded = []
        for r in rows[:max_rows]:
            r = list(r)
            try:
                items = json.loads(r[idx]) if r[idx] else []
                r[idx] = ", ".join(items[:6]) + (" …" if len(items) > 6 else "")
            except Exception:
                pass
            expanded.append(tuple(r))
        rows = expanded

    # Simple tabular print
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows[:max_rows])) for i, c in enumerate(cols)]
    header = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols))
    print(header)
    print("-+-".join("-" * w for w in widths))
    for r in rows[:max_rows]:
        print(" | ".join(str(r[i]).ljust(widths[i]) for i in range(len(cols))))
    if len(rows) > max_rows:
        print(f"... ({len(rows)-max_rows} more rows)")

# ---------- Main loop ----------
if __name__ == "__main__":
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found at {DB_PATH}. Run scripts/init_db.py first.")

    print("🍳 Recipe Finder SQL Assistant (type 'exit' to quit)")
    print(f"What do you want to know about the recipes?")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            break

        try:
            sql = nl_to_sql(user_input)
            sql = clean_sql(sql)
            print(f"\nSQL → {sql}")
            cols, rows = run_sql(sql)
            pretty_print(cols, rows, MAX_ROWS)
            print()
        except Exception as e:
            print(f"⚠️  {e}\n")
