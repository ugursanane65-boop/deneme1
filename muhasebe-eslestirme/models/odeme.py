from datetime import datetime

from models import db


class Odeme(db.Model):
    __tablename__ = "odemeler"

    id = db.Column(db.Integer, primary_key=True)
    odeme_no = db.Column(db.String(50))
    odeme_tarihi = db.Column(db.Date, default=datetime.utcnow)
    tutar = db.Column(db.Float, nullable=False)
    yontem = db.Column(db.String(50))  # havale, kredi karti, nakit vb.
    banka_hesabi = db.Column(db.String(100))
    referans_no = db.Column(db.String(100))
    musteri_id = db.Column(db.Integer, db.ForeignKey("musteriler.id"), nullable=False)

    eslestirmeler = db.relationship("Eslestirme", backref="odeme", lazy=True)

    def __repr__(self):
        return f"<Odeme {self.id} - {self.tutar}>"
