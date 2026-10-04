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

@auth.route("/send_request/<int:user_id>", methods=["POST"])
def send_connection_request(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    sender_id = session["user_id"]

    if sender_id == user_id:
        return "You cannot send a connection request to yourself."

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return "User not found", 404

        cursor.execute(
            """
            SELECT id, status
            FROM connection_requests
            WHERE sender_id = %s AND receiver_id = %s
            """,
            (sender_id, user_id)
        )

        existing = cursor.fetchone()

        if existing:
            if existing["status"] == "pending":
                return "Connection request already pending."

            if existing["status"] == "accepted":
                return "You are already connected."

            if existing["status"] == "removed":
                cursor.execute(
                    """
                    UPDATE connection_requests
                    SET status = 'pending', created_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (existing["id"],)
                )
                connection.commit()
                return "Connection request sent."

        cursor.execute(
            """
            SELECT id, status
            FROM connection_requests
            WHERE sender_id = %s AND receiver_id = %s
            """,
            (user_id, sender_id)
        )

        reverse_request = cursor.fetchone()

        if reverse_request:
            if reverse_request["status"] == "pending":
                return "This user has already sent you a connection request."

            if reverse_request["status"] == "accepted":
                return "You are already connected."

        cursor.execute(
            """
            SELECT id
            FROM blocks
            WHERE (blocker_id = %s AND blocked_id = %s)
               OR (blocker_id = %s AND blocked_id = %s)
            """,
            (sender_id, user_id, user_id, sender_id)
        )

        if cursor.fetchone():
            return "Connection request cannot be sent."

        cursor.execute(
            """
            INSERT INTO connection_requests
            (sender_id, receiver_id, status)
            VALUES (%s, %s, 'pending')
            """,
            (sender_id, user_id)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return "Connection request sent."

@auth.route("/connection_requests")
def connection_requests():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT cr.id, cr.sender_id, u.username, cr.created_at
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = %s
            AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
            """,
            (session["user_id"],)
        )

        requests = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "connection_requests.html",
        requests=requests
    )

@auth.route("/accept_connection/<int:request_id>", methods=["POST"])
def accept_connection_request(request_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM connection_requests
            WHERE id = %s
            AND receiver_id = %s
            AND status = 'pending'
            """,
            (request_id, session["user_id"])
        )

        request_data = cursor.fetchone()

        if not request_data:
            return "Connection request not found.", 404

        cursor.execute(
            """
            UPDATE connection_requests
            SET status = 'accepted'
            WHERE id = %s
            """,
            (request_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("auth.connection_requests"))

@auth.route("/reject_connection/<int:request_id>", methods=["POST"])
def reject_connection_request(request_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM connection_requests
            WHERE id = %s
            AND receiver_id = %s
            AND status = 'pending'
            """,
            (request_id, session["user_id"])
        )

        request_data = cursor.fetchone()

        if not request_data:
            return "Connection request not found.", 404

        cursor.execute(
            """
            UPDATE connection_requests
            SET status = 'rejected'
            WHERE id = %s
            """,
            (request_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("auth.connection_requests"))

@auth.route("/connections")
def connections():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                cr.id AS connection_id,
                u.id AS user_id,
                u.username
            FROM connection_requests cr
            JOIN users u
                ON (
                    (cr.sender_id = %s AND cr.receiver_id = u.id)
                    OR
                    (cr.receiver_id = %s AND cr.sender_id = u.id)
                )
            WHERE cr.status = 'accepted'
            ORDER BY u.username
            """,
            (session["user_id"], session["user_id"])
        )

        connections_list = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "connections.html",
        connections=connections_list
    )

@auth.route("/remove_connection/<int:connection_id>", methods=["POST"])
def remove_connection(connection_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM connection_requests
            WHERE id = %s
            AND status = 'accepted'
            AND (
                sender_id = %s
                OR receiver_id = %s
            )
            """,
            (connection_id, session["user_id"], session["user_id"])
        )

        connection_data = cursor.fetchone()

        if not connection_data:
            return "Connection not found.", 404

        cursor.execute(
            """
            UPDATE connection_requests
            SET status = 'removed'
            WHERE id = %s
            """,
            (connection_id,)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("auth.connections"))

@auth.route("/block/<int:user_id>", methods=["POST"])
def block_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    blocker_id = session["user_id"]

    if blocker_id == user_id:
        return "You cannot block yourself."

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Check user exists
        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )

        if not cursor.fetchone():
            return "User not found.", 404

        # Add block
        cursor.execute(
            """
            INSERT INTO blocks (blocker_id, blocked_id)
            VALUES (%s, %s)
            """,
            (blocker_id, user_id)
        )

        # Remove existing connection, if any
        cursor.execute(
            """
            UPDATE connection_requests
            SET status = 'removed'
            WHERE status = 'accepted'
            AND (
                (sender_id = %s AND receiver_id = %s)
                OR
                (sender_id = %s AND receiver_id = %s)
            )
            """,
            (blocker_id, user_id, user_id, blocker_id)
        )

        connection.commit()

    except Exception as e:
        connection.rollback()

        if getattr(e, "errno", None) == 1062:
            return "User is already blocked."

        return "Failed to block user."

    finally:
        cursor.close()
        connection.close()

    return "User blocked."

@auth.route("/unblock/<int:user_id>", methods=["POST"])
def unblock_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    blocker_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM blocks
            WHERE blocker_id = %s
            AND blocked_id = %s
            """,
            (blocker_id, user_id)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return "User unblocked."

@auth.route("/blocked")
def blocked_users():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                b.blocked_id AS user_id,
                u.username
            FROM blocks b
            JOIN users u
                ON b.blocked_id = u.id
            WHERE b.blocker_id = %s
            ORDER BY u.username
            """,
            (session["user_id"],)
        )

        blocked_users_list = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "blocked.html",
        blocked_users=blocked_users_list
    )