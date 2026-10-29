from flask import Blueprint, render_template

from ..models import Produto

bp = Blueprint("loja", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/catalogo")
def catalogo():
    produtos = Produto.query.order_by(Produto.nome).all()
    return render_template("catalogo.html", produtos=produtos)


@bp.route("/produto/<slug>")
def produto(slug):
    produto = Produto.query.filter_by(slug=slug).first_or_404()
    variantes = sorted(produto.variantes, key=lambda v: v.id)
    padrao = next((v for v in variantes if v.estoque > 0), None)
    return render_template("produto.html", produto=produto, variantes=variantes, padrao=padrao)