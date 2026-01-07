from flask import Flask, jsonify, request
import os
import pyodbc
from datetime import date
import requests
from dotenv import load_dotenv
import hashlib

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = Flask(__name__)

# -----------------------------
# Config
# -----------------------------
AUTH_API_URL = os.environ.get("AUTH_API_URL", "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users")
LOCAL_AUTH_FALLBACK = os.environ.get("LOCAL_AUTH_FALLBACK", "true").lower() == "true"

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
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

def get_conn():
    return pyodbc.connect(connection_string())

# -----------------------------
# Helpers
# -----------------------------
PROFILE_FIELDS = ["Username", "Email", "Location", "PreferredActivity", "DateOfBirth"]
NEW_USER_FIELDS = ["Username"]

def validate_date_iso(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except Exception:
        return False

def get_request_username() -> str | None:
    return request.headers.get("X-User")

def authenticator_lookup(username: str) -> dict | None:
    try:
        r = requests.post(
            AUTH_API_URL,
            json={"username": username},
            timeout=5
        )

        if r.status_code != 200:
            return None

        data = r.json()

        # Auth API returns something like ["Verified", "False"]
        if not data or data[0] != "Verified":
            return None

        # Role assignment
        roles = ["admin", "staff", "user"]
        digest = hashlib.md5(username.encode()).hexdigest()
        role = roles[int(digest, 16) % len(roles)]

        return {
            "username": username,
            "role": role
        }

    except requests.exceptions.RequestException:
        return None

def require_auth():
    username = get_request_username()
    if not username:
        return None, (jsonify({"error": "Missing X-User header"}), 401)

    user = authenticator_lookup(username)
    if not user:
        return None, (jsonify({"error": "Unauthorized user"}), 401)

    return user, None

def require_roles(user: dict, allowed_roles: list[str]):
    if user.get("role") not in allowed_roles:
        return (jsonify({"error": "Forbidden"}), 403)
    return None

def fetch_profile_owner(profile_id: int) -> str | None:
    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("SELECT Username FROM CW2.Profile WHERE ProfileID = ?;", profile_id)
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        cur.close()
        cn.close()

def create_profile_internal(data: dict, message: str = "Profile created"):
    """
    Internal helper to insert a full profile from a request JSON dict.
    Expects keys: Username, Email, Location, PreferredActivity, DateOfBirth
    """
    username = data["Username"].strip()
    email = data["Email"].strip()
    location = data["Location"].strip()
    preferred_activity = data["PreferredActivity"].strip()
    dob = data["DateOfBirth"].strip()

    if not validate_date_iso(dob):
        return jsonify({"error": "DateOfBirth must be ISO format YYYY-MM-DD"}), 400

    cn = get_conn()
    cur = cn.cursor()
    try:
        # prevent duplicate username profile
        cur.execute("SELECT 1 FROM CW2.Profile WHERE Username = ?;", username)
        if cur.fetchone():
            return jsonify({"error": "Profile already exists for this username"}), 409

        cur.execute("""
            INSERT INTO CW2.Profile
                (Username, Email, Location, PreferredActivity, DateOfBirth)
            OUTPUT INSERTED.ProfileID
            VALUES (?, ?, ?, ?, ?);
        """, (username, email, location, preferred_activity, dob))

        row = cur.fetchone()
        new_id = int(row[0]) if row else None
        cn.commit()

        return jsonify({"message": message, "ProfileID": new_id}), 201

    except pyodbc.Error:
        cn.rollback()
        return jsonify({"error": "Database error while creating profile"}), 500
    finally:
        cur.close()
        cn.close()


# -----------------------------
# Routes
# -----------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/openapi", methods=["GET"])
def openapi_hint():
    user, err = require_auth()
    if err:
        return err

    return jsonify({
        "message": "See openapi.yaml in the repository.",
        "auth_header": "X-User",
        "user": user
    }), 200

@app.route("/roles/me", methods=["GET"])
def my_role():
    user, err = require_auth()
    if err:
        return err
    return jsonify({"username": user["username"], "role": user["role"]}), 200

# -----------------------------
# New user requirement
# -----------------------------

@app.route("/users", methods=["POST"])
def create_user():
    """
    New user story: create a profile row with only a username.
    - admin/staff: can create any user
    - user: can only create their own profile
    """
    user, err = require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    username = (data.get("Username") or "").strip()
    if not username:
        return jsonify({"error": "Missing field: Username"}), 400

    # Role rule: users can only create themselves
    if user["role"] == "user" and username != user["username"]:
        return jsonify({"error": "Users can only create their own profile"}), 403

    # Optional: if you want ONLY admin/staff/users (already guaranteed by authenticator_lookup)
    if user["role"] not in ("admin", "staff", "user"):
        return jsonify({"error": "Forbidden"}), 403

    # Validate target exists in Authenticator API
    auth_target = authenticator_lookup(username)
    if not auth_target:
        return jsonify({"error": "Username not found in Authenticator API"}), 400

    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("SELECT 1 FROM CW2.Profile WHERE Username = ?;", username)
        if cur.fetchone():
            return jsonify({"error": "Profile already exists for this username"}), 409

        cur.execute("""
            INSERT INTO CW2.Profile (Username)
            OUTPUT INSERTED.ProfileID
            VALUES (?);
        """, username)

        row = cur.fetchone()
        new_id = int(row[0]) if row else None
        cn.commit()

        return jsonify({
            "message": "User created",
            "ProfileID": new_id,
            "Username": username
        }), 201

    except pyodbc.Error:
        cn.rollback()
        return jsonify({"error": "Database error while creating user"}), 500
    finally:
        cur.close()
        cn.close()

# -----------------------------
# Profiles CRUD (secured)
# -----------------------------
@app.route("/profiles", methods=["GET"])
def get_profiles():
    user, err = require_auth()
    if err:
        return err

    deny = require_roles(user, ["admin", "staff"])
    if deny:
        return deny

    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("""
            SELECT TOP 50
                ProfileID, Username, Email, Location, PreferredActivity, DateOfBirth
            FROM CW2.Profile
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
    user, err = require_auth()
    if err:
        return err

    owner = fetch_profile_owner(profile_id)
    if not owner:
        return jsonify({"error": "Profile not found"}), 404

    if user["role"] == "user" and owner != user["username"]:
        return jsonify({"error": "Forbidden"}), 403

    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("""
            SELECT
                ProfileID, Username, Email, Location, PreferredActivity, DateOfBirth
            FROM CW2.Profile
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
    user, err = require_auth()
    if err:
        return err

    data = request.get_json(silent=True) or {}

    if user["role"] == "user":
        return jsonify({"error": "Use /users to create your profile with username only"}), 403

    missing = [k for k in PROFILE_FIELDS if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    username = (data.get("Username") or "").strip()

    auth_target = authenticator_lookup(username)
    if not auth_target:
        return jsonify({"error": "Username not found in Authenticator API"}), 400

    return create_profile_internal(data, message="Profile created")

@app.route("/profiles/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id: int):
    user, err = require_auth()
    if err:
        return err

    owner = fetch_profile_owner(profile_id)
    if not owner:
        return jsonify({"error": "Profile not found"}), 404

    if user["role"] == "user" and owner != user["username"]:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    location = data.get("Location")
    preferred_activity = data.get("PreferredActivity")

    if location is None and preferred_activity is None:
        return jsonify({"error": "At least one field must be provided"}), 400

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

        sql = f"UPDATE CW2.Profile SET {', '.join(fields)} WHERE ProfileID = ?;"
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
    user, err = require_auth()
    if err:
        return err

    owner = fetch_profile_owner(profile_id)
    if not owner:
        return jsonify({"error": "Profile not found"}), 404

    if user["role"] == "staff":
        return jsonify({"error": "Forbidden"}), 403
    if user["role"] == "user" and owner != user["username"]:
        return jsonify({"error": "Forbidden"}), 403

    cn = get_conn()
    cur = cn.cursor()
    try:
        cur.execute("DELETE FROM CW2.Profile WHERE ProfileID = ?;", profile_id)

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
    app.run(host="0.0.0.0", port=8000)
