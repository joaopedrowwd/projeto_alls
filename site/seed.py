from app import create_app
from app.extensions import db
from app.models import Produto, Usuario, Variante

CORES = ["Azul", "Amarelo", "Branco", "Laranja", "Preto", "Rosa", "Roxo", "Vermelho", "Verde"]

MODELOS = [f"CA {n}" for n in range(3002, 3011)]  # CA 3002 até CA 3010

PRECO_PACOTE = 4500  # centavos (R$ 45,00 por pacote de 100), ajuste por modelo se precisar
ESTOQUE_INICIAL = 50  # pacotes por variante


def seed():
    db.drop_all()
    db.create_all()

    admin = Usuario(nome="Administrador", email="admin@loja.com", role="admin")
    admin.set_senha("admin123")
    cliente = Usuario(nome="João", email="joao@teste.com", role="cliente")
    cliente.set_senha("123456")
    db.session.add_all([admin, cliente])

    for nome in MODELOS:
        slug = nome.lower().replace(" ", "-")  # "CA 3002" -> "ca-3002"
        produto = Produto(
            nome=nome,
            slug=slug,
            descricao=f"Caneta {nome}. Vendida em pacotes de 100 unidades.",
            imagem=f"img/canetas/{slug}.jpg",
            preco_pacote=PRECO_PACOTE,
        )
        produto.variantes = [Variante(cor=c, estoque=ESTOQUE_INICIAL) for c in CORES]
        db.session.add(produto)

    db.session.commit()
    print(f"Seed concluído: 2 usuários, {len(MODELOS)} produtos, {len(MODELOS) * len(CORES)} variantes.")


if __name__ == "__main__":
    with create_app().app_context():
        seed()