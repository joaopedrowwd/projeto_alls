import os
from flask import Flask
from dotenv import load_dotenv
from .utils import COR_HEX, brl, imagem_url

from .extensions import db, login_manager

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///loja.db"

    db.init_app(app)
    login_manager.init_app(app)
    from . import models  # noqa: F401  (registra as tabelas e o user_loader)

    from .loja import bp as loja_bp
    from .auth import bp as auth_bp
    from .admin import bp as admin_bp
    from .carrinho import bp as carrinho_bp
    from .cliente import bp as cliente_bp
    
    app.register_blueprint(carrinho_bp)
    app.register_blueprint(loja_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cliente_bp)

    from .models import UNIDADES_POR_PACOTE

    app.add_template_filter(brl, "brl")
    app.jinja_env.globals["COR_HEX"] = COR_HEX
    app.jinja_env.globals["UNIDADES_POR_PACOTE"] = UNIDADES_POR_PACOTE
    app.jinja_env.globals["imagem_url"] = imagem_url

    return app