"""Fatura ve odeme verilerini dogrulama servisleri."""

PDF_ZORUNLU_ALANLAR = ["fatura_no", "fatura_tarihi", "vergi_no", "unvan", "genel_toplam"]
TUTAR_TOLERANSI = 0.01


def tutar_gecerli_mi(tutar):
    try:
        return float(tutar) > 0
    except (TypeError, ValueError):
        return False


def vergi_no_gecerli_mi(vergi_no):
    if not vergi_no:
        return False
    return vergi_no.isdigit() and len(vergi_no) in (10, 11)


def fatura_verisini_dogrula(fatura_no, tutar, musteri_id):
    hatalar = []
    if not fatura_no:
        hatalar.append("Fatura numarasi zorunludur.")
    if not tutar_gecerli_mi(tutar):
        hatalar.append("Tutar gecerli bir sayi olmalidir.")
    if not musteri_id:
        hatalar.append("Musteri secilmelidir.")
    return hatalar


def odeme_verisini_dogrula(tutar, musteri_id):
    hatalar = []
    if not tutar_gecerli_mi(tutar):
        hatalar.append("Tutar gecerli bir sayi olmalidir.")
    if not musteri_id:
        hatalar.append("Musteri secilmelidir.")
    return hatalar


def pdf_verisini_dogrula(veri):
    """PDF'den cikarilan fatura verisini zorunlu alan ve mantik kurallarina gore dogrular.

    `veri` sozlugu pdf_service.faturadan_veri_cikar ile ayni alan adlarini bekler
    (fatura_no, fatura_tarihi, vade_tarihi, vergi_no, unvan, net_tutar, kdv_orani,
    kdv_tutari, genel_toplam); tarih alanlari `date` nesnesi, tutar alanlari `float`
    olmalidir. Donen sozluk: {"hatalar": [...], "uyarilar": [...], "durum": ...}.
    """
    hatalar = []
    uyarilar = []

    for alan in PDF_ZORUNLU_ALANLAR:
        if veri.get(alan) in (None, ""):
            hatalar.append({"alan": alan, "mesaj": "Zorunlu alan eksik"})

    net_tutar = veri.get("net_tutar")
    kdv_orani = veri.get("kdv_orani")
    kdv_tutari = veri.get("kdv_tutari")
    genel_toplam = veri.get("genel_toplam")
    fatura_tarihi = veri.get("fatura_tarihi")
    vade_tarihi = veri.get("vade_tarihi")

    if net_tutar is not None and kdv_tutari is not None and genel_toplam is not None:
        hesaplanan_toplam = net_tutar + kdv_tutari
        if abs(hesaplanan_toplam - genel_toplam) > TUTAR_TOLERANSI:
            uyarilar.append(
                {
                    "alan": "genel_toplam",
                    "mesaj": f"Tutar uyusmuyor: {genel_toplam} != {hesaplanan_toplam}",
                }
            )

    if net_tutar is not None and kdv_orani is not None and kdv_tutari is not None:
        beklenen_kdv = net_tutar * (kdv_orani / 100)
        if abs(beklenen_kdv - kdv_tutari) > TUTAR_TOLERANSI:
            uyarilar.append(
                {
                    "alan": "kdv_tutari",
                    "mesaj": f"Tutar uyusmuyor: {kdv_tutari} != {beklenen_kdv}",
                }
            )

    if fatura_tarihi is not None and vade_tarihi is not None and vade_tarihi < fatura_tarihi:
        uyarilar.append(
            {
                "alan": "vade_tarihi",
                "mesaj": "Vade tarihi fatura tarihinden once olamaz",
            }
        )

    if genel_toplam is not None and genel_toplam <= 0:
        uyarilar.append(
            {
                "alan": "genel_toplam",
                "mesaj": "Genel toplam sifirdan buyuk olmalidir",
            }
        )

    if hatalar:
        durum = "hata"
    elif uyarilar:
        durum = "uyari"
    else:
        durum = "gecerli"

    return {"hatalar": hatalar, "uyarilar": uyarilar, "durum": durum}
