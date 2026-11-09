import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
JSON_FILE = PROJECT_ROOT / "src" / "data" / "leaders.json"
SQL_FILE = PROJECT_ROOT / "src" / "data" / "seed_leaders.sql"

def generate_sql():
    if not JSON_FILE.exists():
        print(f"Datoteka {JSON_FILE} ne postoji! Prvo pokreni fetch_leaders.py.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        leaders = json.load(f)

    if not leaders:
        print("JSON datoteka je prazna.")
        return

    values_list = []
    for leader in leaders:
        # Eskapiranje apostrofa za imena poput Kin'emon -> Kin''emon
        name = str(leader['name']).replace("'", "''")
        code = str(leader['code']).replace("'", "''")
        color = str(leader['color']).replace("'", "''")
        
        values_list.append(f"  ('{name}', '{code}', '{color}')")

    # Sastavljanje SQL upita (PostgreSQL / SQLite podržavaju ON CONFLICT)
    sql_content = []
    sql_content.append("-- Kreiranje tablice ako već ne postoji")
    sql_content.append("CREATE TABLE IF NOT EXISTS leaders (")
    sql_content.append("    id SERIAL PRIMARY KEY,")
    sql_content.append("    name VARCHAR(255) NOT NULL,")
    sql_content.append("    code VARCHAR(50) UNIQUE NOT NULL,")
    sql_content.append("    color VARCHAR(50) NOT NULL")
    sql_content.append(");\n")
    sql_content.append("-- Masovni unos s preskakanjem postojećih koda")
    sql_content.append("INSERT INTO leaders (name, code, color) VALUES")
    sql_content.append(",\n".join(values_list))
    sql_content.append("\nON CONFLICT (code) DO NOTHING;")

    SQL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SQL_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_content))

    print(f"Uspješno generiran SQL file s {len(leaders)} vođa u:\n{SQL_FILE}")

if __name__ == "__main__":
    generate_sql()