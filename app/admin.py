from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt

from app.db import get_db_connection


admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.before_request
def require_active_admin():
    # The login page is the only admin endpoint that does not require a session.
    if request.endpoint == "admin.admin_login":
        return

    admin_id = session.get("admin_id")
    if admin_id is None:
        return redirect(url_for("admin.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT is_admin, is_active FROM users WHERE id = %s",
            (admin_id,)
        )
        admin_user = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if (
        not admin_user
        or not admin_user["is_admin"]
        or not admin_user["is_active"]
    ):
        session.pop("admin_id", None)
        session.pop("admin_username", None)
        flash("Your admin account is no longer active.", "error")
        return redirect(url_for("admin.admin_login"))


@admin.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT id, username, password_hash, is_admin, is_active
                FROM users
                WHERE username = %s
                """,
                (username,)
            )

            user = cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

        if (
            user
            and user["is_admin"]
            and user["is_active"]
            and bcrypt.checkpw(
                password.encode("utf-8"),
                user["password_hash"].encode("utf-8")
            )
        ):
            session["admin_id"] = user["id"]
            session["admin_username"] = user["username"]

            return redirect(url_for("admin.dashboard"))

        flash("Invalid admin credentials.", "error")

    return render_template("admin/login.html")


@admin.route("/dashboard")
def dashboard():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Dashboard statistics
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS total_users,
                (SELECT COUNT(*) FROM users WHERE is_active = 1) AS active_users,
                (SELECT COUNT(*) FROM users WHERE is_active = 0) AS disabled_users,
                (SELECT COUNT(*) FROM messages) AS total_messages,
                (SELECT COUNT(*) FROM connection_requests
                 WHERE status = 'accepted') AS total_connections
            """
        )

        stats = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin/dashboard.html",
        stats=stats
    )


@admin.route("/users")
def users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, username, is_admin, is_active, created_at, last_seen
            FROM users
            ORDER BY id
            """
        )
        users_list = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template(
        "admin/users.html",
        users=users_list
    )


@admin.route("/toggle-user/<int:user_id>", methods=["POST"])
def toggle_user(user_id):
    if user_id == session["admin_id"]:
        flash("You cannot disable your own admin account.", "error")
        return redirect(url_for("admin.users"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT is_active FROM users WHERE id = %s AND is_admin = 0",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            flash("User not found or cannot be modified.", "error")
            return redirect(url_for("admin.users"))

        new_status = not user["is_active"]

        cursor.execute(
            """
            UPDATE users
            SET is_active = %s
            WHERE id = %s
            """,
            (new_status, user_id)
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    flash("User status updated successfully.", "success")
    return redirect(url_for("admin.users"))

@admin.route("/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    # Prevent deleting any admin account
    if user_id == session["admin_id"]:
        flash("You cannot delete your own admin account.", "error")
        return redirect(url_for("admin.users"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Verify the target is a normal user
        cursor.execute(
            """
            SELECT id, username
            FROM users
            WHERE id = %s
            AND is_admin = 0
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            flash("User not found or cannot be deleted.", "error")
            return redirect(url_for("admin.users"))

        # Delete messages involving the user
        cursor.execute(
            """
            DELETE FROM messages
            WHERE sender_id = %s
               OR receiver_id = %s
            """,
            (user_id, user_id)
        )

        # Delete connection requests involving the user
        cursor.execute(
            """
            DELETE FROM connection_requests
            WHERE sender_id = %s
               OR receiver_id = %s
            """,
            (user_id, user_id)
        )

        # Delete blocks involving the user
        cursor.execute(
            """
            DELETE FROM blocks
            WHERE blocker_id = %s
               OR blocked_id = %s
            """,
            (user_id, user_id)
        )

        # Delete the user account
        cursor.execute(
            """
            DELETE FROM users
            WHERE id = %s
            AND is_admin = 0
            """,
            (user_id,)
        )

        connection.commit()

    except Exception:
        connection.rollback()
        flash("Failed to delete user.", "error")
        return redirect(url_for("admin.users"))

    finally:
        cursor.close()
        connection.close()

    flash(
        f"User '{user['username']}' deleted successfully.",
        "success"
    )

    return redirect(url_for("admin.users"))

@admin.route("/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect(url_for("admin.admin_login"))
