from flask import Blueprint

from ..decorators import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def painel():
    return "Painel do administrador (provisório)"