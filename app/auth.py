import bcrypt
from flask import Blueprint, request, render_template, redirect, url_for

from app.db import get_db_connection


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            return "Username and password are required"

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
            return f"Registration failed: {e}"

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("auth.register"))

    return render_template("register.html")