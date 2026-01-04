import pyodbc
import os

cn = pyodbc.connect(connection_string())
cur = cn.cursor()

cur.execute("SELECT TOP 5 * FROM CW1.vw_ProfileSummary;")
rows = cur.fetchall()

print("Connected ✅")
for r in rows:
    print(r)

cur.close()
cn.close()
