from datetime import datetime

from models import db


class Fatura(db.Model):
    __tablename__ = "faturalar"

    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(50), nullable=False, unique=True)
    fatura_tarihi = db.Column(db.Date, default=datetime.utcnow)
    vade_tarihi = db.Column(db.Date)
    tur = db.Column(db.String(20), default="satis")  # satis, alis
    net_tutar = db.Column(db.Float, nullable=False)
    kdv_orani = db.Column(db.Float, default=0.0)
    kdv_tutari = db.Column(db.Float, default=0.0)
    genel_toplam = db.Column(db.Float, nullable=False)
    para_birimi = db.Column(db.String(10), default="TRY")
    durum = db.Column(db.String(20), default="odenmedi")  # odenmedi, odendi, kismi
    aciklama = db.Column(db.String(255))
    musteri_id = db.Column(db.Integer, db.ForeignKey("musteriler.id"), nullable=False)
    dosya_yolu = db.Column(db.String(255))

    eslestirmeler = db.relationship("Eslestirme", backref="fatura", lazy=True)

    @property
    def kalan(self):
        """Genel toplamdan, faturaya ait tum eslestirmelerin toplamini dusurerek kalan bakiyeyi hesaplar."""
        toplam_eslestirilen = sum(e.eslestirilen_tutar for e in self.eslestirmeler)
        return self.genel_toplam - toplam_eslestirilen

    def __repr__(self):
        return f"<Fatura {self.fatura_no}>"
