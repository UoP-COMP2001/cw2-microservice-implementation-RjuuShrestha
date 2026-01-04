from flask import Flask, jsonify, request
import os
import pyodbc
from datetime import date

app = Flask(__name__)

# -----------------------------
# Database connection
# -----------------------------
def connection_string() -> str:
    server = os.environ.get("DB_SERVER")
    database = os.environ.get("DB_NAME")
    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")

    if not all([server, database, username, password]):
        raise RuntimeError("Missing DB env vars: DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD")

    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

def get_conn():
    return pyodbc.connect(connection_string())


# -----------------------------
# Helpers
# -----------------------------
PROFILE_FIELDS = ["Username", "Email", "Location", "PreferredActivity", "DateOfBirth"]

def validate_date_iso(value: str) -> bool:
    try:
        # expects YYYY-MM-DD
        date.fromisoformat(value)
        return True
    except Exception:
        return False


# -----------------------------
# Routes
# -----------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/profiles", methods=["GET"])
def get_profiles():
    cn = get_conn()
    cur = cn.cursor()
    try:
        # CW2 guidance: DB operations implemented in Python (no stored procs/views)
        cur.execute("""
            SELECT TOP 50
                ProfileID, Username, Email, Location, PreferredActivity, DateOfBirth
            FROM CW1.Profile
            ORDER BY ProfileID DESC;
        """)
        columns = [col[0] for col in cur.description]
        rows = cur.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        return jsonify(data), 200
    finally:
        cur.close()
        cn.close()


@app.route("/profiles/<int:profile_id>", methods=["GET"])
def get_profile(profile_id: int):
    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("""
            SELECT
                ProfileID, Username, Email, Location, PreferredActivity, DateOfBirth
            FROM CW1.Profile
            WHERE ProfileID = ?;
        """, profile_id)

        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Profile not found"}), 404

        columns = [col[0] for col in cur.description]
        data = dict(zip(columns, row))
        return jsonify(data), 200
    finally:
        cur.close()
        cn.close()


@app.route("/profiles", methods=["POST"])
def create_profile():
    data = request.get_json(silent=True) or {}

    missing = [k for k in PROFILE_FIELDS if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    username = data.get("Username")
    email = data.get("Email")
    location = data.get("Location")
    preferred_activity = data.get("PreferredActivity")
    date_of_birth = data.get("DateOfBirth")

    # Basic validation
    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "Username must be a non-empty string"}), 400
    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Email must be a non-empty string"}), 400
    if not isinstance(location, str) or not location.strip():
        return jsonify({"error": "Location must be a non-empty string"}), 400
    if not isinstance(preferred_activity, str) or not preferred_activity.strip():
        return jsonify({"error": "PreferredActivity must be a non-empty string"}), 400
    if not isinstance(date_of_birth, str) or not validate_date_iso(date_of_birth):
        return jsonify({"error": "DateOfBirth must be in YYYY-MM-DD format"}), 400

    cn = get_conn()
    cur = cn.cursor()
    try:
        # Insert directly (no stored procedure), return created ID
        cur.execute("""
            INSERT INTO CW1.Profile (Username, Email, Location, PreferredActivity, DateOfBirth)
            OUTPUT INSERTED.ProfileID
            VALUES (?, ?, ?, ?, ?);
        """, username, email, location, preferred_activity, date_of_birth)

        row = cur.fetchone()
        new_id = int(row[0]) if row else None

        cn.commit()
        return jsonify({"message": "Profile created", "ProfileID": new_id}), 201
    except pyodbc.Error:
        cn.rollback()
        # Keeps error generic to avoid leaking DB details
        return jsonify({"error": "Database error while creating profile"}), 500
    finally:
        cur.close()
        cn.close()


@app.route("/profiles/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id: int):
    data = request.get_json(silent=True) or {}

    location = data.get("Location")
    preferred_activity = data.get("PreferredActivity")

    # Partial update supported: at least one field
    if location is None and preferred_activity is None:
        return jsonify({"error": "At least one field must be provided"}), 400

    # Optional validation
    if location is not None and (not isinstance(location, str) or not location.strip()):
        return jsonify({"error": "Location must be a non-empty string"}), 400
    if preferred_activity is not None and (not isinstance(preferred_activity, str) or not preferred_activity.strip()):
        return jsonify({"error": "PreferredActivity must be a non-empty string"}), 400

    cn = get_conn()
    cur = cn.cursor()
    try:
        fields = []
        params = []

        if location is not None:
            fields.append("Location = ?")
            params.append(location)

        if preferred_activity is not None:
            fields.append("PreferredActivity = ?")
            params.append(preferred_activity)

        params.append(profile_id)

        sql = f"UPDATE CW1.Profile SET {', '.join(fields)} WHERE ProfileID = ?;"
        cur.execute(sql, params)

        if cur.rowcount == 0:
            cn.rollback()
            return jsonify({"error": "Profile not found"}), 404

        cn.commit()
        return jsonify({"message": "Profile updated"}), 200
    except pyodbc.Error:
        cn.rollback()
        return jsonify({"error": "Database error while updating profile"}), 500
    finally:
        cur.close()
        cn.close()


@app.route("/profiles/<int:profile_id>", methods=["DELETE"])
def delete_profile(profile_id: int):
    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("DELETE FROM CW1.Profile WHERE ProfileID = ?;", profile_id)

        if cur.rowcount == 0:
            cn.rollback()
            return jsonify({"error": "Profile not found"}), 404

        cn.commit()
        return ("", 204)
    except pyodbc.Error:
        cn.rollback()
        return jsonify({"error": "Database error while deleting profile"}), 500
    finally:
        cur.close()
        cn.close()


if __name__ == "__main__":
    # Host/port aligned with OpenAPI server URL
    app.run(host="0.0.0.0", port=8000)
