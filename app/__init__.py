import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from app.admin import admin
from app.auth import auth


load_dotenv()


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = os.getenv("SECRET_KEY")

    # Enable CSRF protection
    CSRFProtect(app)

    app.register_blueprint(auth)
    app.register_blueprint(admin)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template(
            "error.html",
            code=404,
            message="Page not found."
        ), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template(
            "error.html",
            code=500,
            message="Something went wrong. Please try again later."
        ), 500

    return app