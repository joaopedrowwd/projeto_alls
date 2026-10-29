from flask import Blueprint, jsonify, render_template, request, session

from ..extensions import db
from ..models import UNIDADES_POR_PACOTE, Variante

bp = Blueprint("carrinho", __name__, url_prefix="/carrinho")

CHAVE = "carrinho"  # session["carrinho"] = {"<variante_id>": pacotes}


def _ler():
    return dict(session.get(CHAVE, {}))


def _salvar(dados):
    session[CHAVE] = dados
    session.modified = True


def detalhar():
    """Monta o carrinho a partir do banco (preços e estoque sempre atuais).
    Remove itens inválidos e ajusta quantidades que passaram do estoque."""
    dados = _ler()
    variantes = {}
    if dados:
        ids = [int(k) for k in dados]
        variantes = {v.id: v for v in Variante.query.filter(Variante.id.in_(ids)).all()}

    itens, limpo = [], {}
    for chave, pacotes in dados.items():
        v = variantes.get(int(chave))
        if not v or v.estoque < 1:
            continue
        pacotes = max(1, min(int(pacotes), v.estoque))
        limpo[chave] = pacotes
        itens.append({
            "variante": v,
            "produto": v.produto,
            "pacotes": pacotes,
            "unidades": pacotes * UNIDADES_POR_PACOTE,
            "subtotal": pacotes * v.produto.preco_pacote,
        })

    if limpo != dados:
        _salvar(limpo)

    return {
        "itens": itens,
        "total": sum(i["subtotal"] for i in itens),
        "contador": sum(i["pacotes"] for i in itens),
    }


@bp.app_context_processor
def injetar_carrinho():
    """Deixa a variável `carrinho` disponível em todos os templates."""
    return {"carrinho": detalhar()}


def _resposta(tipo, mensagem="", status=200):
    c = detalhar()
    return jsonify(
        ok=status < 400,
        tipo=tipo,
        mensagem=mensagem,
        contador=c["contador"],
        html=render_template("_carrinho_conteudo.html", carrinho=c),
    ), status


def _inteiro(nome):
    try:
        return int(request.form.get(nome, ""))
    except ValueError:
        return None


@bp.post("/adicionar")
def adicionar():
    vid, pacotes = _inteiro("variante_id"), _inteiro("pacotes")
    if vid is None or pacotes is None or pacotes < 1:
        return _resposta("error", "Quantidade inválida.", 400)

    v = db.session.get(Variante, vid)
    if not v:
        return _resposta("error", "Produto não encontrado.", 404)
    if v.estoque < 1:
        return _resposta("error", "Esta cor está esgotada.", 400)

    dados = _ler()
    chave = str(vid)
    novo = dados.get(chave, 0) + pacotes
    nome = f"{v.produto.nome} ({v.cor})"

    if novo > v.estoque:
        dados[chave] = v.estoque
        _salvar(dados)
        return _resposta("warning", f"Limite de estoque: {v.estoque} pacotes de {nome}.")

    dados[chave] = novo
    _salvar(dados)
    return _resposta("success", f"{nome} adicionado ao carrinho.")


@bp.post("/alterar")
def alterar():
    vid, pacotes = _inteiro("variante_id"), _inteiro("pacotes")
    dados = _ler()
    if vid is None or pacotes is None or str(vid) not in dados:
        return _resposta("error", "Item não encontrado no carrinho.", 404)

    v = db.session.get(Variante, vid)
    if not v or v.estoque < 1:
        dados.pop(str(vid), None)
        _salvar(dados)
        return _resposta("warning", "Este item não está mais disponível.")

    dados[str(vid)] = max(1, min(pacotes, v.estoque))
    _salvar(dados)
    return _resposta("info")


@bp.post("/remover")
def remover():
    vid = _inteiro("variante_id")
    dados = _ler()
    dados.pop(str(vid), None)
    _salvar(dados)
    return _resposta("info", "Item removido.")