from datetime import datetime

from models import db


class Eslestirme(db.Model):
    __tablename__ = "eslestirmeler"

    id = db.Column(db.Integer, primary_key=True)
    odeme_id = db.Column(db.Integer, db.ForeignKey("odemeler.id"), nullable=False)
    fatura_id = db.Column(db.Integer, db.ForeignKey("faturalar.id"), nullable=False)
    eslestirilen_tutar = db.Column(db.Float, nullable=False)
    eslestirme_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    kalan_bakiye = db.Column(db.Float, default=0.0)
    durum = db.Column(db.String(20), default="bekliyor")  # tam, kismi, bekliyor
    olusturan = db.Column(db.String(100))

    def __repr__(self):
        return f"<Eslestirme fatura={self.fatura_id} odeme={self.odeme_id}>"
