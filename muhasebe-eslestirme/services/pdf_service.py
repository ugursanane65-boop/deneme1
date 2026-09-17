"""PDF faturalardan veri okuma ve cikarma servisleri."""

import re
from datetime import datetime

import pdfplumber

ALAN_ADLARI = [
    "fatura_no",
    "fatura_tarihi",
    "vade_tarihi",
    "vergi_no",
    "unvan",
    "net_tutar",
    "kdv_orani",
    "kdv_tutari",
    "genel_toplam",
]

# Alan basina, PDF metninde aranacak (etiket, deger) yakalama deseni.
_DESENLER = {
    "fatura_no": r"Fatura\s*No\s*[:\-]?\s*([A-Za-z0-9\-/]+)",
    "fatura_tarihi": r"Fatura\s*Tarihi\s*[:\-]?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
    "vade_tarihi": r"Vade\s*Tarihi\s*[:\-]?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
    "vergi_no": r"Vergi\s*(?:No|Numaras[ıi])\s*[:\-]?\s*(\d{10,11})",
    "unvan": r"(?:Unvan|Firma\s*Unvan[ıi])\s*[:\-]?\s*([^\n]+)",
    "net_tutar": r"Net\s*Tutar\s*[:\-]?\s*([\d.,]+)",
    "kdv_orani": r"KDV\s*Oran[ıi]\s*[:\-]?\s*([\d.,]+)\s*%?",
    "kdv_tutari": r"KDV\s*Tutar[ıi]\s*[:\-]?\s*([\d.,]+)",
    "genel_toplam": r"Genel\s*Toplam\s*[:\-]?\s*([\d.,]+)",
}


def pdf_metnini_oku(dosya_yolu):
    """Verilen PDF dosyasindan ham metni okur."""
    metin = ""
    with pdfplumber.open(dosya_yolu) as pdf:
        for sayfa in pdf.pages:
            sayfa_metni = sayfa.extract_text()
            if sayfa_metni:
                metin += sayfa_metni + "\n"
    return metin


def _alan_bul(desen, metin):
    eslesme = re.search(desen, metin, re.IGNORECASE)
    return eslesme.group(1).strip() if eslesme else None


def _tarihi_cevir(deger):
    if not deger:
        return None
    for format_ in ("%d.%m.%Y", "%d/%m/%Y", "%d.%m.%y", "%d/%m/%y"):
        try:
            return datetime.strptime(deger, format_).date()
        except ValueError:
            continue
    return None


def _sayiyi_cevir(deger):
    if not deger:
        return None
    temiz = deger.replace(".", "").replace(",", ".")
    try:
        return float(temiz)
    except ValueError:
        return None


def faturadan_veri_cikar(dosya_yolu):
    """PDF faturadan alanlari cikarir; bulunamayan alanlar None ve eksik olarak isaretlenir.

    Donen sozluk: fatura_no, fatura_tarihi, vade_tarihi, vergi_no, unvan, net_tutar,
    kdv_orani, kdv_tutari, genel_toplam ve bulunamayan alan adlarini iceren eksik_alanlar.
    """
    metin = pdf_metnini_oku(dosya_yolu)
    ham_degerler = {alan: _alan_bul(_DESENLER[alan], metin) for alan in ALAN_ADLARI}

    veri = {
        "fatura_no": ham_degerler["fatura_no"],
        "fatura_tarihi": _tarihi_cevir(ham_degerler["fatura_tarihi"]),
        "vade_tarihi": _tarihi_cevir(ham_degerler["vade_tarihi"]),
        "vergi_no": ham_degerler["vergi_no"],
        "unvan": ham_degerler["unvan"],
        "net_tutar": _sayiyi_cevir(ham_degerler["net_tutar"]),
        "kdv_orani": _sayiyi_cevir(ham_degerler["kdv_orani"]),
        "kdv_tutari": _sayiyi_cevir(ham_degerler["kdv_tutari"]),
        "genel_toplam": _sayiyi_cevir(ham_degerler["genel_toplam"]),
    }
    veri["eksik_alanlar"] = [alan for alan in ALAN_ADLARI if veri[alan] is None]

    return veri
