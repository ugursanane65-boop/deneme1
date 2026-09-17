"""Fatura - odeme eslestirme algoritmalari."""

from models import db
from models.eslestirme import Eslestirme
from models.fatura import Fatura
from models.odeme import Odeme


def _eslesmis_odeme_idler():
    return {e.odeme_id for e in Eslestirme.query.all()}


def otomatik_eslestir(olusturan="sistem"):
    """Odenmemis faturalari, eslestirilmemis odemelerle ayni musteri ve tutar uzerinden otomatik eslestirir."""
    olusturulan = []
    faturalar = Fatura.query.filter(Fatura.durum != "odendi").all()
    kullanilan_odeme_idler = _eslesmis_odeme_idler()
    odemeler = [o for o in Odeme.query.all() if o.id not in kullanilan_odeme_idler]

    for fatura in faturalar:
        for odeme in odemeler:
            if odeme.id in kullanilan_odeme_idler:
                continue
            if fatura.musteri_id == odeme.musteri_id and fatura.genel_toplam == odeme.tutar:
                eslestirme = Eslestirme(
                    fatura_id=fatura.id,
                    odeme_id=odeme.id,
                    eslestirilen_tutar=odeme.tutar,
                    kalan_bakiye=0.0,
                    durum="tam",
                    olusturan=olusturan,
                )
                fatura.durum = "odendi"
                kullanilan_odeme_idler.add(odeme.id)
                db.session.add(eslestirme)
                olusturulan.append(eslestirme)
                break

    db.session.commit()
    return olusturulan


def manuel_eslestir(fatura_id, odeme_id, tutar, olusturan="kullanici"):
    fatura = Fatura.query.get(fatura_id)
    kalan_bakiye = (fatura.genel_toplam - tutar) if fatura else 0.0
    durum = "tam" if kalan_bakiye <= 0 else "kismi"
    eslestirme = Eslestirme(
        fatura_id=fatura_id,
        odeme_id=odeme_id,
        eslestirilen_tutar=tutar,
        kalan_bakiye=kalan_bakiye,
        durum=durum,
        olusturan=olusturan,
    )
    db.session.add(eslestirme)
    db.session.commit()
    return eslestirme


def eslestir(odeme_id, fatura_id, tutar, olusturan="kullanici"):
    """Bir odemeyi bir faturayla verilen tutar uzerinden eslestirir, faturanin durumunu gunceller."""
    odeme = Odeme.query.get(odeme_id)
    fatura = Fatura.query.get(fatura_id)

    if not odeme or not fatura:
        return {"basarili": False, "hata": "Odeme veya fatura bulunamadi."}

    if fatura.durum == "odendi":
        return {"basarili": False, "hata": "Fatura zaten tam olarak odenmis durumda."}

    if tutar > odeme.tutar:
        return {"basarili": False, "hata": "Eslestirilen tutar, odeme tutarindan buyuk olamaz."}

    eslestirme = Eslestirme(
        odeme_id=odeme_id,
        fatura_id=fatura_id,
        eslestirilen_tutar=tutar,
        olusturan=olusturan,
    )
    db.session.add(eslestirme)
    db.session.flush()

    toplam_eslestirilen = sum(
        e.eslestirilen_tutar for e in Eslestirme.query.filter_by(fatura_id=fatura_id).all()
    )
    kalan = fatura.genel_toplam - toplam_eslestirilen

    fatura.durum = "odendi" if kalan <= 0 else "kismi"
    eslestirme.durum = "tam" if kalan <= 0 else "kismi"
    eslestirme.kalan_bakiye = kalan

    db.session.commit()

    return {
        "basarili": True,
        "hata": None,
        "eslestirme": eslestirme,
        "kalan": kalan,
        "fatura_durum": fatura.durum,
    }


def bekleyen_faturalar(musteri_id):
    """Belirtilen musteriye ait, durumu 'odenmedi' veya 'kismi' olan faturalari listeler."""
    return Fatura.query.filter(
        Fatura.musteri_id == musteri_id,
        Fatura.durum.in_(["odenmedi", "kismi"]),
    ).order_by(Fatura.fatura_tarihi.desc()).all()


def eslestirme_ozeti(fatura_id):
    """Faturanin tum eslestirmelerini, eslestirilen toplami ve kalan bakiyeyi dondurur."""
    fatura = Fatura.query.get(fatura_id)
    if not fatura:
        return None

    eslestirmeler = (
        Eslestirme.query.filter_by(fatura_id=fatura_id)
        .order_by(Eslestirme.eslestirme_tarihi)
        .all()
    )
    toplam_eslestirilen = sum(e.eslestirilen_tutar for e in eslestirmeler)
    kalan = fatura.genel_toplam - toplam_eslestirilen

    return {
        "fatura_id": fatura_id,
        "eslestirmeler": eslestirmeler,
        "toplam_eslestirilen": toplam_eslestirilen,
        "kalan": kalan,
        "durum": fatura.durum,
    }
