import sqlite3
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, role) VALUES (1, 'admin', 'superuser')")
    conn.commit()
    conn.close()


@app.route("/user", methods=["GET"])
def get_user():
    username = request.args.get("username", "")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    query = "SELECT id, username, role FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"id": user[0], "username": user[1], "role": user[2]})
    return jsonify({"error": "User not found"}), 404


@app.route("/ping", methods=["GET"])
def ping_host():
    host = request.args.get("host", "127.0.0.1")
    output = subprocess.check_output(["ping", "-c", "1", host], shell=False, text=True)
    return jsonify({"result": output})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000)
