from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from models.eslestirme import Eslestirme
from models.fatura import Fatura
from models.odeme import Odeme
from services.eslestirme_service import (
    bekleyen_faturalar,
    eslestir,
    eslestirme_ozeti,
    otomatik_eslestir,
)

eslestirme_bp = Blueprint("eslestirme", __name__, url_prefix="/eslestirmeler")


@eslestirme_bp.route("/")
def liste():
    eslestirmeler = Eslestirme.query.order_by(Eslestirme.eslestirme_tarihi.desc()).all()
    return render_template("eslestirme_list.html", eslestirmeler=eslestirmeler)


@eslestirme_bp.route("/manuel")
def manuel():
    faturalar = Fatura.query.filter(Fatura.durum.in_(["odenmedi", "kismi"])).order_by(
        Fatura.fatura_tarihi.desc()
    ).all()
    eslesmis_odeme_idler = {e.odeme_id for e in Eslestirme.query.all()}
    odemeler = [o for o in Odeme.query.order_by(Odeme.odeme_tarihi.desc()).all() if o.id not in eslesmis_odeme_idler]
    return render_template("eslestirme.html", faturalar=faturalar, odemeler=odemeler)


@eslestirme_bp.route("/otomatik-calistir", methods=["POST"])
def otomatik_calistir():
    otomatik_eslestir()
    return redirect(url_for("eslestirme.liste"))


@eslestirme_bp.route("/eslestir", methods=["POST"])
def eslestir_route():
    girdi = request.get_json(silent=True) or request.form.to_dict() or {}
    odeme_id = girdi.get("odeme_id")
    fatura_id = girdi.get("fatura_id")
    tutar = girdi.get("tutar")

    if not odeme_id or not fatura_id or tutar is None:
        return jsonify({"hata": "odeme_id, fatura_id ve tutar zorunludur."}), 400

    try:
        odeme_id = int(odeme_id)
        fatura_id = int(fatura_id)
        tutar = float(tutar)
    except (TypeError, ValueError):
        return jsonify({"hata": "odeme_id ve fatura_id tam sayi, tutar sayisal olmalidir."}), 400

    sonuc = eslestir(odeme_id, fatura_id, tutar)
    if not sonuc["basarili"]:
        return jsonify(sonuc), 400

    return (
        jsonify(
            {
                "basarili": True,
                "eslestirme_id": sonuc["eslestirme"].id,
                "kalan": sonuc["kalan"],
                "fatura_durum": sonuc["fatura_durum"],
            }
        ),
        201,
    )


@eslestirme_bp.route("/bekleyen/<int:musteri_id>")
def bekleyen(musteri_id):
    faturalar = bekleyen_faturalar(musteri_id)
    return jsonify(
        [
            {
                "id": f.id,
                "fatura_no": f.fatura_no,
                "genel_toplam": f.genel_toplam,
                "kalan": f.kalan,
                "durum": f.durum,
            }
            for f in faturalar
        ]
    )


@eslestirme_bp.route("/ozet/<int:fatura_id>")
def ozet(fatura_id):
    sonuc = eslestirme_ozeti(fatura_id)
    if sonuc is None:
        return jsonify({"hata": "Fatura bulunamadi."}), 404

    return jsonify(
        {
            "fatura_id": sonuc["fatura_id"],
            "toplam_eslestirilen": sonuc["toplam_eslestirilen"],
            "kalan": sonuc["kalan"],
            "durum": sonuc["durum"],
            "eslestirmeler": [
                {
                    "id": e.id,
                    "odeme_id": e.odeme_id,
                    "eslestirilen_tutar": e.eslestirilen_tutar,
                    "eslestirme_tarihi": e.eslestirme_tarihi.isoformat() if e.eslestirme_tarihi else None,
                    "durum": e.durum,
                }
                for e in sonuc["eslestirmeler"]
            ],
        }
    )
