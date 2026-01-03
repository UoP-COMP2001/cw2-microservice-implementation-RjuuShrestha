from flask import Flask, jsonify
from flask import request
import pyodbc
from config import connection_string
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/profiles", methods=["GET"])
def get_profiles():
    cn = pyodbc.connect(connection_string())
    cur = cn.cursor()

    cur.execute("SELECT TOP 50 * FROM CW1.vw_ProfileSummary;")
    columns = [col[0] for col in cur.description]
    rows = cur.fetchall()

    data = [dict(zip(columns, row)) for row in rows]

    cur.close()
    cn.close()

    return jsonify(data), 200

@app.route("/profiles/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    cn = pyodbc.connect(connection_string())
    cur = cn.cursor()

    cur.execute("SELECT * FROM CW1.vw_ProfileSummary WHERE ProfileID = ?", profile_id)
    columns = [col[0] for col in cur.description]
    rows = cur.fetchall()

    data = [dict(zip(columns, row)) for row in rows]

    cur.close()
    cn.close()

    if not data:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(data), 200

@app.route("/profiles", methods=["POST"])
def create_profile():
    data = request.get_json()

    username = data["Username"]
    email = data["Email"]
    location = data["Location"]
    preferred_activity = data["PreferredActivity"]
    date_of_birth = data["DateOfBirth"]

    conn = pyodbc.connect(connection_string())
    cursor = conn.cursor()

    cursor.execute(
    "EXEC CW1.sp_AddProfile @Username=?, @Email=?, @Location=?, @PreferredActivity=?, @DateOfBirth=?",
    username,
    email,
    location,
    preferred_activity,
    date_of_birth
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Profile created"}), 201

@app.route("/profiles/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id):
    data = request.get_json(silent=True) or {}

    location = data.get("Location")
    preferred_activity = data.get("PreferredActivity")

    if not location or not preferred_activity:
        return jsonify({"error": "Location and PreferredActivity are required"}), 400

    cn = pyodbc.connect(connection_string())
    cur = cn.cursor()

    cur.execute(
        "EXEC CW1.sp_UpdateProfile @ProfileID=?, @Location=?, @PreferredActivity=?",
        profile_id, location, preferred_activity
    )
    cn.commit()

    cur.close()
    cn.close()

    return jsonify({"message": "Profile updated"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
