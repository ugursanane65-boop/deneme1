from models import db


class HesapPlani(db.Model):
    __tablename__ = "hesap_plani"

    id = db.Column(db.Integer, primary_key=True)
    hesap_kodu = db.Column(db.String(20), nullable=False, unique=True)
    hesap_adi = db.Column(db.String(150), nullable=False)
    hesap_turu = db.Column(db.String(50))  # varlik, borc, ozkaynak, gelir, gider vb.
    borc = db.Column(db.Float, default=0.0)
    alacak = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<HesapPlani {self.hesap_kodu} - {self.hesap_adi}>"
