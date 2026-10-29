import os
from flask import Flask, render_template
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
    from .models import UNIDADES_POR_PACOTE
    
    app.register_blueprint(carrinho_bp)
    app.register_blueprint(loja_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cliente_bp)
    app.add_template_filter(brl, "brl")
    app.jinja_env.globals["COR_HEX"] = COR_HEX
    app.jinja_env.globals["UNIDADES_POR_PACOTE"] = UNIDADES_POR_PACOTE
    app.jinja_env.globals["imagem_url"] = imagem_url

    @app.errorhandler(403)
    def erro_403(_e):
        return render_template(
            "erro.html",
            codigo=403,
            titulo="Acesso restrito",
            mensagem="Você não tem permissão para acessar esta área.",
        ), 403

    @app.errorhandler(404)
    def erro_404(_e):
        return render_template(
            "erro.html",
            codigo=404,
            titulo="Página não encontrada",
            mensagem="O endereço que você tentou acessar não existe ou foi removido.",
        ), 404

    return app