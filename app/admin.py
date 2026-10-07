from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt

from app.auth import get_db_connection


admin = Blueprint("admin", __name__, url_prefix="/admin")


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
    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT is_active
            FROM users
            WHERE id = %s
            AND is_admin = 1
            """,
            (session["admin_id"],)
        )

        admin_user = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not admin_user or not admin_user["is_active"]:
        session.pop("admin_id", None)
        session.pop("admin_username", None)

        flash("Your admin account has been disabled.", "error")
        return redirect(url_for("admin.admin_login"))

    return render_template("admin/dashboard.html")


@admin.route("/users")
def users():
    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

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
    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

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


@admin.route("/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect(url_for("admin.admin_login"))