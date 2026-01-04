import pyodbc
import os

def connection_string() -> str:
    server = os.environ.get("DB_SERVER")
    database = os.environ.get("DB_NAME")
    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")

    if not all([server, database, username, password]):
        raise RuntimeError("Database environment variables are not fully set")

    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )

def main():
    cn = pyodbc.connect(connection_string())
    cur = cn.cursor()

    cur.execute("SELECT TOP 5 * FROM CW2.Profile;")
    rows = cur.fetchall()

    print("Connected ✅")
    for r in rows:
        print(r)

    cur.close()
    cn.close()

if __name__ == "__main__":
    main()
