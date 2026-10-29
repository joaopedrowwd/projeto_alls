import os

from flask import current_app, url_for

COR_HEX = {
    "Azul": "#2563eb",
    "Amarelo": "#facc15",
    "Branco": "#ffffff",
    "Laranja": "#f97316",
    "Preto": "#111827",
    "Rosa": "#ec4899",
    "Roxo": "#7c3aed",
    "Vermelho": "#dc2626",
    "Verde": "#16a34a",
}

EXTENSOES = ("jpg", "jpeg", "png", "webp")


def brl(centavos):
    """4500 -> 'R$ 45,00'  |  123456 -> 'R$ 1.234,56'"""
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def imagem_url(slug, cor=None):
    """URL da foto do modelo na cor pedida. Sem cor, devolve a primeira que existir.
    Devolve None se não houver arquivo."""
    pasta = os.path.join(current_app.static_folder, "img", "canetas", slug)
    cores = [cor] if cor else list(COR_HEX)
    for c in cores:
        for ext in EXTENSOES:
            nome = f"{c.lower()}.{ext}"
            if os.path.exists(os.path.join(pasta, nome)):
                return url_for("static", filename=f"img/canetas/{slug}/{nome}")
    return None