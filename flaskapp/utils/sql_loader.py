from pathlib import Path

def load_sql(relative_path: str) -> str:
    base_dir = Path(__file__).resolve().parent.parent  # flaskapp/
    sql_path = base_dir / relative_path
    with open(sql_path, encoding='utf-8') as f:
        return f.read()