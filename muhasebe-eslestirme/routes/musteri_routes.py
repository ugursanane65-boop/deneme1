from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from models import db
from models.musteri import Musteri

musteri_bp = Blueprint("musteri", __name__, url_prefix="/musteriler")


def _form_verisi(form):
    return {
        "unvan": (form.get("unvan") or "").strip(),
        "vergi_no": (form.get("vergi_no") or "").strip(),
        "vergi_dairesi": (form.get("vergi_dairesi") or "").strip() or None,
        "tur": form.get("tur") or "musteri",
        "iban": (form.get("iban") or "").strip() or None,
        "email": (form.get("email") or "").strip() or None,
        "telefon": (form.get("telefon") or "").strip() or None,
        "adres": (form.get("adres") or "").strip() or None,
    }


def _musteri_verisini_dogrula(veri, mevcut_id=None):
    if not veri["unvan"]:
        return "Ünvan zorunludur"
    if not veri["vergi_no"]:
        return "Vergi No zorunludur"

    sorgu = Musteri.query.filter_by(vergi_no=veri["vergi_no"])
    if mevcut_id is not None:
        sorgu = sorgu.filter(Musteri.id != mevcut_id)
    if sorgu.first():
        return "Bu vergi numarası zaten kayıtlı"
    return None


@musteri_bp.route("/")
def liste():
    q = request.args.get("q", "").strip()
    filtre = request.args.get("filtre", "aktif")
    sorgu = Musteri.query
    if filtre == "pasif":
        sorgu = sorgu.filter_by(aktif=False)
    elif filtre == "hepsi":
        pass
    else:
        filtre = "aktif"
        sorgu = sorgu.filter_by(aktif=True)
    if q:
        arama = f"%{q}%"
        sorgu = sorgu.filter(db.or_(Musteri.unvan.ilike(arama), Musteri.vergi_no.ilike(arama)))
    musteriler = sorgu.order_by(Musteri.aktif.desc(), Musteri.unvan).all()
    return render_template("musteriler/liste.html", musteriler=musteriler, q=q, filtre=filtre)


@musteri_bp.route("/yeni", methods=["GET", "POST"])
def yeni():
    if request.method == "POST":
        veri = _form_verisi(request.form)
        hata = _musteri_verisini_dogrula(veri)
        if hata:
            flash(hata, "hata")
            return render_template("musteriler/form.html", musteri=None, form_data=veri)

        musteri = Musteri(**veri)
        db.session.add(musteri)
        db.session.commit()
        flash("Müşteri başarıyla kaydedildi.", "basari")
        return redirect(url_for("musteri.liste"))

    return render_template("musteriler/form.html", musteri=None, form_data=None)


@musteri_bp.route("/<int:musteri_id>/duzenle", methods=["GET", "POST"])
def duzenle(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)

    if request.method == "POST":
        veri = _form_verisi(request.form)
        hata = _musteri_verisini_dogrula(veri, mevcut_id=musteri_id)
        if hata:
            flash(hata, "hata")
            return render_template("musteriler/form.html", musteri=musteri, form_data=veri)

        for alan, deger in veri.items():
            setattr(musteri, alan, deger)
        db.session.commit()
        flash("Müşteri başarıyla güncellendi.", "basari")
        return redirect(url_for("musteri.liste"))

    return render_template("musteriler/form.html", musteri=musteri, form_data=None)


@musteri_bp.route("/<int:musteri_id>/sil", methods=["POST"])
def sil(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)
    musteri.aktif = False
    db.session.commit()
    flash("Müşteri pasife alındı.", "basari")
    return redirect(url_for("musteri.liste", filtre="aktif"))


@musteri_bp.route("/<int:musteri_id>/aktif-yap", methods=["POST"])
def aktif_yap(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)
    musteri.aktif = True
    db.session.commit()
    flash(f"{musteri.unvan} aktif hale getirildi.", "basari")
    return redirect(url_for("musteri.liste", filtre="pasif"))


@musteri_bp.route("/ara")
def ara():
    q = request.args.get("q", "").strip()
    filtre = request.args.get("filtre", "aktif")

    if len(q) < 2:
        return jsonify([])

    arama = f"%{q}%"

    sorgu = Musteri.query.filter(
        db.or_(Musteri.unvan.ilike(arama), Musteri.vergi_no.ilike(arama))
    )

    if filtre == "aktif":
        sorgu = sorgu.filter_by(aktif=True)
    elif filtre == "pasif":
        sorgu = sorgu.filter_by(aktif=False)

    sonuclar = sorgu.order_by(Musteri.unvan).limit(20).all()

    return jsonify(
        [
            {
                "id": m.id,
                "unvan": m.unvan,
                "vergi_no": m.vergi_no,
                "tur": m.tur,
                "email": m.email or "",
                "aktif": m.aktif,
            }
            for m in sonuclar
        ]
    )
