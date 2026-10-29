import os
from flask import Flask
from dotenv import load_dotenv

from .extensions import db

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///loja.db"

    db.init_app(app)
    from . import models  # noqa: F401  (registra as tabelas)

    from .loja import bp as loja_bp
    app.register_blueprint(loja_bp)

    return app