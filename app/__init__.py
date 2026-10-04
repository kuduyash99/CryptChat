import os
from flask import Flask, render_template
from dotenv import load_dotenv

from app.auth import auth

load_dotenv()


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = os.getenv("SECRET_KEY")

    app.register_blueprint(auth)

    @app.route("/")
    def home():
        return render_template("index.html")

    return app