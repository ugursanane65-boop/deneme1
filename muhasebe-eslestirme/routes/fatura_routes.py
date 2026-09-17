from datetime import datetime
import os

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from models import db
from models.fatura import Fatura
from models.musteri import Musteri
from services.dogrulama_service import fatura_verisini_dogrula, pdf_verisini_dogrula
from services.pdf_service import faturadan_veri_cikar

fatura_bp = Blueprint("fatura", __name__, url_prefix="/faturalar")

IZIN_VERILEN_UZANTILAR = {"pdf"}


def _uzanti_gecerli_mi(dosya_adi):
    return "." in dosya_adi and dosya_adi.rsplit(".", 1)[1].lower() in IZIN_VERILEN_UZANTILAR


def _pdf_dosyasini_kaydet_ve_isle(dosya, musteri_id):
    """Yuklenen PDF'i diske kaydeder, veri cikarir ve zorunlu alanlar tamsa Fatura olusturur.

    Donen deger: (veri, eksik_alanlar, dosya_yolu, fatura|None)
    """
    dosya_adi = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(dosya.filename)}"
    upload_klasoru = current_app.config["UPLOAD_FOLDER"]
    dosya_yolu = os.path.join(upload_klasoru, dosya_adi)
    dosya.save(dosya_yolu)

    veri = faturadan_veri_cikar(dosya_yolu)

    zorunlu_alanlar = {"fatura_no", "net_tutar", "genel_toplam"}
    eksik_alanlar = list(veri["eksik_alanlar"])
    if not musteri_id:
        eksik_alanlar.append("musteri_id")

    if zorunlu_alanlar.intersection(eksik_alanlar) or "musteri_id" in eksik_alanlar:
        return veri, eksik_alanlar, dosya_yolu, None

    fatura = Fatura(
        fatura_no=veri["fatura_no"],
        fatura_tarihi=veri["fatura_tarihi"] or datetime.utcnow().date(),
        vade_tarihi=veri["vade_tarihi"],
        net_tutar=veri["net_tutar"],
        kdv_orani=veri["kdv_orani"] or 0.0,
        kdv_tutari=veri["kdv_tutari"] or 0.0,
        genel_toplam=veri["genel_toplam"],
        musteri_id=int(musteri_id),
        dosya_yolu=dosya_yolu,
    )
    db.session.add(fatura)
    db.session.commit()
    return veri, eksik_alanlar, dosya_yolu, fatura


@fatura_bp.route("/")
def liste():
    faturalar = Fatura.query.order_by(Fatura.fatura_tarihi.desc()).all()
    return render_template("fatura_list.html", faturalar=faturalar)


@fatura_bp.route("/ekle", methods=["GET", "POST"])
def ekle():
    musteriler = Musteri.query.filter_by(aktif=True).order_by(Musteri.unvan).all()

    if request.method == "POST":
        fatura_no = request.form.get("fatura_no")
        net_tutar = request.form.get("net_tutar")
        kdv_orani = request.form.get("kdv_orani") or 0
        musteri_id = request.form.get("musteri_id")

        hatalar = fatura_verisini_dogrula(fatura_no, net_tutar, musteri_id)
        if hatalar:
            return render_template("fatura_form.html", musteriler=musteriler, hatalar=hatalar)

        net_tutar = float(net_tutar)
        kdv_orani = float(kdv_orani)
        kdv_tutari = net_tutar * kdv_orani / 100
        genel_toplam = net_tutar + kdv_tutari

        fatura = Fatura(
            fatura_no=fatura_no,
            tur=request.form.get("tur", "satis"),
            net_tutar=net_tutar,
            kdv_orani=kdv_orani,
            kdv_tutari=kdv_tutari,
            genel_toplam=genel_toplam,
            para_birimi=request.form.get("para_birimi", "TRY"),
            musteri_id=int(musteri_id),
            aciklama=request.form.get("aciklama"),
        )
        db.session.add(fatura)
        db.session.commit()
        return redirect(url_for("fatura.liste"))

    return render_template("fatura_form.html", musteriler=musteriler, hatalar=[])


@fatura_bp.route("/yukle", methods=["POST"])
def yukle():
    if "dosya" not in request.files:
        return jsonify({"hata": "Yuklenecek dosya bulunamadi."}), 400

    dosya = request.files["dosya"]
    if not dosya.filename:
        return jsonify({"hata": "Dosya secilmedi."}), 400

    if not _uzanti_gecerli_mi(dosya.filename):
        return jsonify({"hata": "Sadece .pdf dosyalari kabul edilir."}), 400

    musteri_id = request.form.get("musteri_id")
    veri, eksik_alanlar, dosya_yolu, fatura = _pdf_dosyasini_kaydet_ve_isle(dosya, musteri_id)

    if fatura is None:
        return jsonify(
            {
                "kaydedildi": False,
                "mesaj": "Fatura eksik alanlar nedeniyle kaydedilmedi, formu tamamlayin.",
                "veri": {k: v for k, v in veri.items() if k != "eksik_alanlar"},
                "eksik_alanlar": eksik_alanlar,
                "dosya_yolu": dosya_yolu,
            }
        ), 200

    return jsonify(
        {
            "kaydedildi": True,
            "fatura_id": fatura.id,
            "veri": {k: v for k, v in veri.items() if k != "eksik_alanlar"},
            "eksik_alanlar": eksik_alanlar,
            "dosya_yolu": dosya_yolu,
        }
    ), 201


@fatura_bp.route("/yukle-sayfa", methods=["GET", "POST"])
def yukle_sayfa():
    musteriler = Musteri.query.filter_by(aktif=True).order_by(Musteri.unvan).all()

    if request.method == "GET":
        return render_template("fatura_yukle.html", musteriler=musteriler)

    if "dosya" not in request.files or not request.files["dosya"].filename:
        return render_template(
            "dogrulama_sonuc.html",
            durum="hata",
            hatalar=[{"alan": "dosya", "mesaj": "Yuklenecek PDF dosyasi secilmedi."}],
            uyarilar=[],
            veri=None,
            kaydedildi=False,
        )

    dosya = request.files["dosya"]
    if not _uzanti_gecerli_mi(dosya.filename):
        return render_template(
            "dogrulama_sonuc.html",
            durum="hata",
            hatalar=[{"alan": "dosya", "mesaj": "Sadece .pdf dosyalari kabul edilir."}],
            uyarilar=[],
            veri=None,
            kaydedildi=False,
        )

    musteri_id = request.form.get("musteri_id")
    veri, eksik_alanlar, dosya_yolu, fatura = _pdf_dosyasini_kaydet_ve_isle(dosya, musteri_id)
    dogrulama = pdf_verisini_dogrula(veri)

    return render_template(
        "dogrulama_sonuc.html",
        durum=dogrulama["durum"],
        hatalar=dogrulama["hatalar"],
        uyarilar=dogrulama["uyarilar"],
        veri=veri,
        kaydedildi=fatura is not None,
        fatura=fatura,
        eksik_alanlar=eksik_alanlar,
    )


def _dogrulama_icin_tarih(deger):
    if isinstance(deger, str):
        try:
            return datetime.strptime(deger, "%Y-%m-%d").date()
        except ValueError:
            return None
    return deger


def _dogrulama_icin_sayi(deger):
    if deger is None or deger == "":
        return None
    try:
        return float(deger)
    except (TypeError, ValueError):
        return None


@fatura_bp.route("/dogrula", methods=["POST"])
def dogrula():
    girdi = request.get_json(silent=True) or request.form.to_dict() or {}

    veri = {
        "fatura_no": girdi.get("fatura_no") or None,
        "fatura_tarihi": _dogrulama_icin_tarih(girdi.get("fatura_tarihi")),
        "vade_tarihi": _dogrulama_icin_tarih(girdi.get("vade_tarihi")),
        "vergi_no": girdi.get("vergi_no") or None,
        "unvan": girdi.get("unvan") or None,
        "net_tutar": _dogrulama_icin_sayi(girdi.get("net_tutar")),
        "kdv_orani": _dogrulama_icin_sayi(girdi.get("kdv_orani")),
        "kdv_tutari": _dogrulama_icin_sayi(girdi.get("kdv_tutari")),
        "genel_toplam": _dogrulama_icin_sayi(girdi.get("genel_toplam")),
    }

    sonuc = pdf_verisini_dogrula(veri)
    return jsonify(sonuc), 200
