from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager

UNIDADES_POR_PACOTE = 100

STATUS_PEDIDO = ["Pago", "Em separação", "Enviado", "Entregue", "Cancelado"]
FRETES = {
    "Retirada": {"valor": 0, "prazo": "Retire na indústria, sem custo"},
    "Padrão": {"valor": 4000, "prazo": "5 a 8 dias úteis"},
    "Expresso": {"valor": 5000, "prazo": "2 a 3 dias úteis"},
}

# Todos os valores em dinheiro são guardados em CENTAVOS (inteiro).
# Evita erro de arredondamento e o aviso do SQLite sobre Decimal.


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="cliente")  # cliente | admin

    pedidos = db.relationship("Pedido", back_populates="usuario")

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.role == "admin"

@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text, default="")
    imagem = db.Column(db.String(200), default="")
    preco_pacote = db.Column(db.Integer, nullable=False)  # centavos

    variantes = db.relationship(
        "Variante", back_populates="produto", cascade="all, delete-orphan"
    )


class Variante(db.Model):
    __table_args__ = (db.UniqueConstraint("produto_id", "cor"),)

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    cor = db.Column(db.String(30), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)  # em pacotes

    produto = db.relationship("Produto", back_populates="variantes")


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pago")
    endereco = db.Column(db.String(255), nullable=False)
    entrega = db.Column(db.String(30), nullable=False)  # Retirada | Padrão | Expresso
    frete = db.Column(db.Integer, nullable=False, default=0)  # centavos
    total = db.Column(db.Integer, nullable=False)  # centavos, já com frete
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)
    lido_admin = db.Column(db.Boolean, nullable=False, default=False)

    usuario = db.relationship("Usuario", back_populates="pedidos")
    itens = db.relationship(
        "ItemPedido", back_populates="pedido", cascade="all, delete-orphan"
    )


class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey("variante.id"), nullable=False)
    pacotes = db.Column(db.Integer, nullable=False)
    preco_pacote = db.Column(db.Integer, nullable=False)  # preço no momento da compra

    pedido = db.relationship("Pedido", back_populates="itens")
    variante = db.relationship("Variante")