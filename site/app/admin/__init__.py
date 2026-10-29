from datetime import datetime, time
from functools import wraps
from flask import (Blueprint, abort, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import STATUS_PEDIDO, ItemPedido, Pedido, Produto, Variante

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not getattr(current_user, "is_admin", False) and getattr(current_user, "role", "") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated

@bp.route("/")
@bp.route("/painel")
@admin_required
def painel():
    hoje_inicio = datetime.combine(datetime.now().date(), time.min)

    # Pedidos válidos (não cancelados)
    pedidos_validos = Pedido.query.filter(Pedido.status != "Cancelado").all()
    pedidos_hoje = [p for p in pedidos_validos if p.criado_em and p.criado_em >= hoje_inicio]

    faturamento_total = sum(p.total for p in pedidos_validos)
    faturamento_hoje = sum(p.total for p in pedidos_hoje)
    ticket_medio = (faturamento_total // len(pedidos_validos)) if pedidos_validos else 0

    # Contagem por status
    contagem_status = {st: 0 for st in STATUS_PEDIDO}
    for p in Pedido.query.all():
        contagem_status[p.status] = contagem_status.get(p.status, 0) + 1

    pendentes_envio = contagem_status.get("Pago", 0) + contagem_status.get("Em separação", 0)
    nao_lidos = Pedido.query.filter_by(lido_admin=False).count()

    # Variantes com estoque baixo (<= 10 pacotes)
    estoque_baixo = (
        Variante.query
        .join(Produto)
        .filter(Variante.estoque <= 10)
        .order_by(Variante.estoque.asc(), Produto.nome.asc())
        .all()
    )

    # Top 5 produtos/cores mais vendidos (em pacotes, ignorando cancelados)
    mais_vendidos = (
        db.session.query(
            Variante,
            func.coalesce(func.sum(ItemPedido.pacotes), 0).label("pacotes_vendidos"),
        )
        .join(ItemPedido, ItemPedido.variante_id == Variante.id)
        .join(Pedido, Pedido.id == ItemPedido.pedido_id)
        .filter(Pedido.status != "Cancelado")
        .group_by(Variante.id)
        .order_by(func.sum(ItemPedido.pacotes).desc())
        .limit(5)
        .all()
    )

    ultimos_pedidos = (
        Pedido.query
        .order_by(Pedido.criado_em.desc(), Pedido.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        pedidos_hoje_qtd=len(pedidos_hoje),
        pedidos_total_qtd=len(pedidos_validos),
        faturamento_hoje=faturamento_hoje,
        faturamento_total=faturamento_total,
        ticket_medio=ticket_medio,
        pendentes_envio=pendentes_envio,
        nao_lidos=nao_lidos,
        contagem_status=contagem_status,
        estoque_baixo=estoque_baixo,
        mais_vendidos=mais_vendidos,
        ultimos_pedidos=ultimos_pedidos,
    )


@bp.route("/estoque/<int:variante_id>", methods=["POST"])
@admin_required
def ajustar_estoque(variante_id):
    variante = db.session.get(Variante, variante_id) or abort(404)
    try:
        novo_estoque = int(request.form.get("estoque", ""))
        if novo_estoque < 0:
            raise ValueError
    except ValueError:
        flash("Informe uma quantidade de estoque válida (0 ou mais).", "error")
        return redirect(request.referrer or url_for("admin.painel"))

    variante.estoque = novo_estoque
    db.session.commit()
    flash(
        f"Estoque de {variante.produto.nome} ({variante.cor}) atualizado para {novo_estoque} pacotes.",
        "success",
    )
    return redirect(request.referrer or url_for("admin.painel"))

@bp.route("/pedidos")
@admin_required
def pedidos():
    status_filtro = request.args.get("status", "").strip()
    query = Pedido.query

    if status_filtro == "nao_lidos":
        query = query.filter_by(lido_admin=False)
    elif status_filtro in STATUS_PEDIDO:
        query = query.filter_by(status=status_filtro)

    lista = query.order_by(Pedido.lido_admin.asc(), Pedido.criado_em.desc(), Pedido.id.desc()).all()
    return render_template(
        "admin/pedidos.html",
        pedidos=lista,
        status_opcoes=STATUS_PEDIDO,
        status_filtro=status_filtro,
    )


@bp.route("/pedidos/<int:pedido_id>/status", methods=["POST"])
@admin_required
def alterar_status(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    novo_status = request.form.get("status", "").strip()

    if novo_status not in STATUS_PEDIDO:
        flash("Status inválido.", "error")
        return redirect(request.referrer or url_for("admin.pedidos"))

    status_anterior = pedido.status
    if status_anterior != novo_status:
        # Se cancelar um pedido que estava ativo, devolve os pacotes ao estoque
        if novo_status == "Cancelado" and status_anterior != "Cancelado":
            for item in pedido.itens:
                Variante.query.filter_by(id=item.variante_id).update(
                    {Variante.estoque: Variante.estoque + item.pacotes},
                    synchronize_session=False,
                )
        # Se reativar um pedido que estava Cancelado, tenta abater o estoque novamente
        elif status_anterior == "Cancelado" and novo_status != "Cancelado":
            for item in pedido.itens:
                afetadas = (
                    Variante.query
                    .filter(Variante.id == item.variante_id, Variante.estoque >= item.pacotes)
                    .update({Variante.estoque: Variante.estoque - item.pacotes}, synchronize_session=False)
                )
                if afetadas != 1:
                    db.session.rollback()
                    flash(
                        f"Estoque insuficiente de {item.variante.produto.nome} ({item.variante.cor}) "
                        "para reativar este pedido.",
                        "error",
                    )
                    return redirect(request.referrer or url_for("admin.pedidos"))

        pedido.status = novo_status

    pedido.lido_admin = True
    db.session.commit()
    flash(f"Pedido #{pedido.id:05d} atualizado para '{novo_status}'.", "success")
    return redirect(request.referrer or url_for("admin.pedidos"))


@bp.route("/pedidos/marcar-lidos", methods=["POST"])
@admin_required
def marcar_lidos():
    Pedido.query.filter_by(lido_admin=False).update(
        {Pedido.lido_admin: True}, synchronize_session=False
    )
    db.session.commit()
    flash("Todas as notificações foram marcadas como lidas.", "success")
    return redirect(request.referrer or url_for("admin.pedidos"))


@bp.route("/notificacoes")
@admin_required
def notificacoes():
    nao_lidos = (
        Pedido.query
        .filter_by(lido_admin=False)
        .order_by(Pedido.criado_em.desc(), Pedido.id.desc())
        .all()
    )
    return jsonify({
        "contador": len(nao_lidos),
        "pedidos": [
            {
                "id": p.id,
                "codigo": f"#{p.id:05d}",
                "cliente": p.usuario.nome if p.usuario else f"Cliente #{p.usuario_id}",
                "total_centavos": p.total,
                "criado_em": p.criado_em.strftime("%d/%m %H:%M"),
            }
            for p in nao_lidos[:5]
        ],
    })