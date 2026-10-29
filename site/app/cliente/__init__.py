import re

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required

from ..carrinho import detalhar, limpar as limpar_carrinho
from ..extensions import db
from ..models import FRETES, ItemPedido, Pedido, Variante

bp = Blueprint("cliente", __name__)

CAMPOS = ("entrega", "cep", "rua", "numero", "complemento", "bairro", "cidade", "uf")


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    c = detalhar()
    if not c["itens"]:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("loja.catalogo"))

    form = {"entrega": "Padrão"}

    if request.method == "POST":
        form = {campo: request.form.get(campo, "").strip() for campo in CAMPOS}
        entrega = form["entrega"]
        cep = re.sub(r"\D", "", form["cep"])

        erros = []
        if entrega not in FRETES:
            erros.append("Escolha uma forma de entrega.")
        elif entrega != "Retirada":
            if len(cep) != 8:
                erros.append("Informe um CEP válido (8 números).")
            for campo, rotulo in (("rua", "a rua"), ("numero", "o número"),
                                  ("bairro", "o bairro"), ("cidade", "a cidade")):
                if not form[campo]:
                    erros.append(f"Informe {rotulo}.")
            if len(form["uf"]) != 2 or not form["uf"].isalpha():
                erros.append("Informe a UF com 2 letras.")

        # O cliente viu um subtotal na tela; se o servidor calcula outro, os dados mudaram
        if not erros and request.form.get("subtotal_visto") != str(c["total"]):
            erros.append("Os valores do carrinho mudaram. Revise o resumo e confirme de novo.")

        if not erros:
            if entrega == "Retirada":
                endereco = "Retirada na indústria"
            else:
                compl = f" - {form['complemento']}" if form["complemento"] else ""
                endereco = (f"{form['rua']}, {form['numero']}{compl} - {form['bairro']}, "
                            f"{form['cidade']}/{form['uf'].upper()} - CEP {cep[:5]}-{cep[5:]}")

            frete = FRETES[entrega]["valor"]

            # Abate o estoque só se ainda houver saldo (UPDATE condicional, seguro contra compras simultâneas)
            for item in c["itens"]:
                afetadas = (
                    Variante.query
                    .filter(Variante.id == item["variante"].id,
                            Variante.estoque >= item["pacotes"])
                    .update({Variante.estoque: Variante.estoque - item["pacotes"]},
                            synchronize_session=False)
                )
                if afetadas != 1:
                    db.session.rollback()
                    flash(f"O estoque de {item['produto'].nome} ({item['variante'].cor}) "
                          "acabou de mudar. Revise seu carrinho.", "error")
                    return redirect(url_for("cliente.checkout"))

            pedido = Pedido(
                usuario_id=current_user.id,
                status="Pago",
                endereco=endereco,
                entrega=entrega,
                frete=frete,
                total=c["total"] + frete,
                lido_admin=False,  # dispara o sino do admin (dia 8)
            )
            for item in c["itens"]:
                pedido.itens.append(ItemPedido(
                    variante_id=item["variante"].id,
                    pacotes=item["pacotes"],
                    preco_pacote=item["produto"].preco_pacote,  # preço no momento da compra
                ))
            db.session.add(pedido)
            db.session.commit()

            limpar_carrinho()
            return redirect(url_for("cliente.pedido_confirmado", pedido_id=pedido.id))

        for erro in erros:
            flash(erro, "error")

    return render_template("checkout.html", form=form, fretes=FRETES)


@bp.route("/pedido/<int:pedido_id>/confirmado")
@login_required
def pedido_confirmado(pedido_id):
    pedido = db.session.get(Pedido, pedido_id)
    if not pedido or (pedido.usuario_id != current_user.id and not current_user.is_admin):
        abort(404)
    return render_template("pedido_confirmado.html", pedido=pedido)


@bp.route("/meus-pedidos")
@login_required
def meus_pedidos():
    pedidos = (
        Pedido.query
        .filter_by(usuario_id=current_user.id)
        .order_by(Pedido.criado_em.desc(), Pedido.id.desc())
        .all()
    )
    return render_template("meus_pedidos.html", pedidos=pedidos)