import bcrypt
import re
from flask import Blueprint, request, render_template, redirect, url_for, session
from app.db import get_db_connection


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        # Username validation
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
            return "Invalid username. Use 3-30 characters: letters, numbers, or underscore only."

        # Password validation
        if len(password) < 8:
            return "Password must be at least 8 characters long."

        if not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter."

        if not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter."

        if not re.search(r"[0-9]", password):
            return "Password must contain at least one number."

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash)
            )

            connection.commit()

        except Exception as e:
            connection.rollback()

            if getattr(e, "errno", None) == 1062:
                return "Username already exists."

            return "Registration failed."

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,)
            )

            user = cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        ):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return f"Login successful. Welcome {user['username']}!"

        return "Invalid username or password"

    return render_template("login.html")

@auth.route("/profile")
def profile():
    if "user_id" not in session:
        return "Not logged in"

    return f"Logged in as {session['username']}"

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth.route("/search")
def search_users():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    query = request.args.get("username", "").strip()

    users = []

    if query:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT id, username
                FROM users
                WHERE username LIKE %s
                AND id != %s
                ORDER BY username
                LIMIT 20
                """,
                (f"%{query}%", session["user_id"])
            )

            users = cursor.fetchall()

        finally:
            cursor.close()
            connection.close()

    return render_template("search.html", users=users, query=query)

@auth.route("/chat/<int:user_id>")
def chat(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, username FROM users WHERE id = %s",
            (user_id,)
        )

        user = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not user:
        return "User not found", 404

    if user["id"] == session["user_id"]:
        return "You cannot chat with yourself."

    return render_template("chat.html", user=user)