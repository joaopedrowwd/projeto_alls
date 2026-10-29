from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Usuario

bp = Blueprint("auth", __name__)


def _destino_seguro(destino):
    """Aceita só caminhos internos (evita redirecionar para outro site)."""
    if destino and destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return destino
    return None


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("loja.index"))

    nome = email = ""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")

        erros = []
        if len(nome) < 2:
            erros.append("Informe seu nome.")
        if "@" not in email or "." not in email:
            erros.append("Informe um e-mail válido.")
        if len(senha) < 6:
            erros.append("A senha precisa ter pelo menos 6 caracteres.")
        if senha != confirmar:
            erros.append("As senhas não conferem.")
        if not erros and Usuario.query.filter_by(email=email).first():
            erros.append("Este e-mail já está cadastrado.")

        if erros:
            for erro in erros:
                flash(erro, "error")
        else:
            usuario = Usuario(nome=nome, email=email, role="cliente")  # cadastro público é sempre cliente
            usuario.set_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("loja.index"))

    return render_template("cadastro.html", nome=nome, email=email)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("loja.index"))

    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_senha(senha):
            login_user(usuario)
            destino = _destino_seguro(request.args.get("next"))
            if destino:
                return redirect(destino)
            if usuario.is_admin:
                return redirect(url_for("admin.painel"))
            return redirect(url_for("loja.index"))

        flash("E-mail ou senha incorretos.", "error")

    return render_template("login.html", email=email)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("loja.index"))