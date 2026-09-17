from datetime import datetime

from models import db


class Musteri(db.Model):
    __tablename__ = "musteriler"

    id = db.Column(db.Integer, primary_key=True)
    unvan = db.Column(db.String(200), nullable=False)
    vergi_no = db.Column(db.String(20), unique=True, nullable=False)
    vergi_dairesi = db.Column(db.String(100))
    tur = db.Column(db.String(20), default="musteri")  # musteri, tedarikci, her_ikisi
    iban = db.Column(db.String(50))
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(30))
    adres = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    faturalar = db.relationship("Fatura", backref="musteri", lazy=True)
    odemeler = db.relationship("Odeme", backref="musteri", lazy=True)

    def __repr__(self):
        return f"<Musteri {self.unvan}>"
