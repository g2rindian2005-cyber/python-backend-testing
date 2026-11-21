from flask import Flask, request, jsonify
import pymysql
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
CORS(app)

# ---------------- DATABASE CONFIG ----------------
db_config = {
    "host": os.getenv("DB_HOST", "database-1.czockkuoo2fx.ap-northeast-1.rds.amazonaws.com"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "cloud123"),
    "database": os.getenv("DB_NAME", "cloud"),
}

def get_db_connection():
    return pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
    )

# ---------------- HOME / HEALTH ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "running", "message": "Flask API is up"}), 200

@app.route("/health", methods=["GET"])
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)}), 500

# ---------------- SIGNUP ----------------
@app.route("/api/signup", methods=["POST"])
def signup():
    conn = None
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already registered"}), 400

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password),
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# ---------------- LOGIN ----------------
@app.route("/api/login", methods=["POST"])
def login():
    conn = None
    try:
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                },
            }), 200
        return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# ---------------- GET ALL USERS ----------------
@app.route("/api/users", methods=["GET"])
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
