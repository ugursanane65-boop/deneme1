from flask import Blueprint, redirect, render_template, request, url_for

from models import db
from models.musteri import Musteri
from models.odeme import Odeme
from services.dogrulama_service import odeme_verisini_dogrula

odeme_bp = Blueprint("odeme", __name__, url_prefix="/odemeler")


@odeme_bp.route("/")
def liste():
    odemeler = Odeme.query.order_by(Odeme.odeme_tarihi.desc()).all()
    return render_template("odeme_list.html", odemeler=odemeler)


@odeme_bp.route("/ekle", methods=["GET", "POST"])
def ekle():
    musteriler = Musteri.query.filter_by(aktif=True).order_by(Musteri.unvan).all()

    if request.method == "POST":
        tutar = request.form.get("tutar")
        musteri_id = request.form.get("musteri_id")
        yontem = request.form.get("yontem")

        hatalar = odeme_verisini_dogrula(tutar, musteri_id)
        if hatalar:
            return render_template("odeme_form.html", musteriler=musteriler, hatalar=hatalar)

        odeme = Odeme(
            odeme_no=request.form.get("odeme_no"),
            tutar=float(tutar),
            musteri_id=int(musteri_id),
            yontem=yontem,
            banka_hesabi=request.form.get("banka_hesabi"),
            referans_no=request.form.get("referans_no"),
        )
        db.session.add(odeme)
        db.session.commit()
        return redirect(url_for("odeme.liste"))

    return render_template("odeme_form.html", musteriler=musteriler, hatalar=[])
