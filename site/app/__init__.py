import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    from .loja import bp as loja_bp
    app.register_blueprint(loja_bp)

    return app