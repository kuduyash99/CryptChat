from flask import Flask, render_template
from app.auth import auth


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.register_blueprint(auth)

    @app.route("/")
    def home():
        return render_template("index.html")

    return app