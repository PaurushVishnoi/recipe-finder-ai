import os, re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_LIMIT = 25

SYSTEM_PROMPT = (
    "You convert natural language to ONE SQLite SELECT statement for the table below.\n"
    "Return ONLY SQL text. No markdown, backticks, or comments.\n"
    "Add a LIMIT if the user doesn't provide one.\n\n"
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

def nl_to_sql(query: str, limit: int | None = None) -> str:
    user = (
        f"Question: {query}\n"
        f"If filtering text columns (title, cuisine, category, author), you may use COLLATE NOCASE.\n"
        f"If no LIMIT is present, append 'LIMIT {limit or DEFAULT_LIMIT}'."
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user","content":user}],
        temperature=0
    )
    return resp.choices[0].message.content.strip()

def clean_sql(text: str) -> str:
    t = text.strip()
    m = re.search(r"```(?:sql)?\s*(.*?)\s*```", t, flags=re.S | re.I)
    if m:
        t = m.group(1).strip()
    t = t.replace("`", "").strip()
    if ";" in t:
        t = t.split(";", 1)[0].strip() + ";"
    if not t.upper().startswith("SELECT"):
        raise ValueError(f"Refusing to execute non-SELECT SQL: {t}")
    return t
