# Muhasebe Eşleştirme — Proje Bağlamı

## Amaç
Bu proje, işletmelerin kestiği **faturalar** ile aldıkları **ödemeleri** otomatik/manuel
olarak eşleştirmesini sağlayan bir muhasebe yardımcı uygulamasıdır. Uygulama; müşteri,
hesap, fatura ve ödeme kayıtlarını tutar, PDF faturalardan veri okuma altyapısı sunar,
girilen verileri doğrular ve fatura-ödeme eşleştirmesini (aynı müşteri + aynı tutar
kuralına göre) otomatik olarak gerçekleştirir. Eşleştirilemeyen kayıtlar için manuel
eşleştirme imkânı da sunulur.

## Teknolojiler
- **Dil:** Python 3
- **Framework:** Flask (blueprint tabanlı, `create_app` factory paterni)
- **ORM:** Flask-SQLAlchemy
- **Veritabanı:** SQLite (`muhasebe.db`, `config.py` üzerinden yapılandırılır)
- **PDF okuma:** pdfplumber (`services/pdf_service.py`)
- **Şablon motoru:** Jinja2 (Flask ile birlikte gelir)
- **Stil:** Sadece gri tonlarda (renksiz) el yazımı CSS — `static/css/main.css`
  Kullanılan palet: `#111, #333, #555, #888, #aaa, #ddd, #f4f4f4, #fff`

## Klasör Yapısı
```
muhasebe-eslestirme/
├── app.py                     # Flask app factory, blueprint kaydı, DB init
├── config.py                  # Config sınıfı (SECRET_KEY, SQLALCHEMY_DATABASE_URI)
├── context.md                 # Bu dosya — proje bağlamı ve güncelleme günlüğü
├── requirements.txt           # Python bağımlılıkları
├── models/
│   ├── __init__.py            # db = SQLAlchemy() ve model importları
│   ├── musteri.py              # Musteri modeli
│   ├── hesap_plani.py           # HesapPlani modeli
│   ├── fatura.py                # Fatura modeli
│   ├── odeme.py                 # Odeme modeli
│   └── eslestirme.py            # Eslestirme (fatura-odeme ilişki) modeli
├── routes/
│   ├── __init__.py
│   ├── fatura_routes.py         # /faturalar blueprint (liste, ekle, yukle, yukle-sayfa, dogrula)
│   ├── odeme_routes.py          # /odemeler blueprint (liste, ekle)
│   ├── eslestirme_routes.py     # /eslestirmeler blueprint (liste, manuel, otomatik çalıştır, eslestir)
│   └── musteri_routes.py        # /musteriler blueprint (liste, yeni, duzenle, sil, ara)
├── services/
│   ├── __init__.py
│   ├── pdf_service.py           # PDF'den metin/fatura verisi okuma
│   ├── dogrulama_service.py      # Fatura/ödeme veri doğrulama kuralları
│   └── eslestirme_service.py     # Otomatik/manuel eşleştirme algoritması
├── templates/
│   ├── base.html                 # Sidebar navigasyon + içerik alanı (ortak layout)
│   ├── index.html                # Anasayfa
│   ├── fatura_list.html / fatura_form.html
│   ├── fatura_yukle.html         # PDF yükleme formu + sürükle-bırak alanı
│   ├── dogrulama_sonuc.html      # PDF doğrulama sonucu (hata/uyarı/başarı kartları)
│   ├── odeme_list.html / odeme_form.html
│   ├── eslestirme_list.html      # Otomatik eşleştirme geçmişi tablosu
│   ├── eslestirme.html           # Manuel eşleştirme ekranı (sol: bekleyen faturalar,
│   │                             #   sağ: ödemeler, ortada eşleştir butonu)
│   └── musteriler/
│       ├── liste.html            # Müşteri tablosu (arama kutusu + Yeni Müşteri butonu)
│       └── form.html             # Yeni/Düzenle ortak formu
└── static/
    └── css/main.css               # Gri tonlarda tüm stil tanımları
```

## Şablon (Template) Yapısı

- **`base.html`**: Sol tarafta sabit (sticky) `sidebar` (koyu `#111` arka plan, `.sidebar-nav`
  linkleri, aktif sayfa `.active` sınıfıyla vurgulanır — `request.endpoint` karşılaştırmasıyla),
  sağ tarafta `.main-area` içinde `.content` (asıl sayfa içeriği) ve altta `.site-footer`.
  Tüm diğer şablonlar bu dosyayı `{% extends "base.html" %}` ile miras alır ve
  `{% block content %}` içine kendi içeriklerini yazar. 800px altında sidebar yatay bara
  dönüşür (responsive, `main.css` içindeki `@media (max-width: 800px)`).
- **`fatura_yukle.html`**: `GET/POST /faturalar/yukle-sayfa` (bkz. `fatura_routes.yukle_sayfa`)
  tarafından render edilir. Müşteri `<select>`'i + `.dropzone` sürükle-bırak alanı (gizli
  `<input type="file">` üstünde `<label>`); saf JS ile `dragenter/dragover/dragleave/drop`
  olayları dinlenip dosya adı `.file-info` kutusunda gösterilir. Form normal
  `multipart/form-data` POST ile aynı route'a gönderilir (AJAX yok), sunucu tarafında
  PDF işlenip sonuç `dogrulama_sonuc.html` olarak döner.
- **`dogrulama_sonuc.html`**: `fatura.yukle_sayfa` POST sonucunu gösterir. `hatalar` listesi
  koyu gri (`.sonuc-item.hata`, sol kenarlık `#333`), `uyarilar` listesi açık gri
  (`.sonuc-item.uyari`, sol kenarlık `#888`) kutular halinde satır satır listelenir; kırmızı
  KULLANILMAZ. `durum == "gecerli"` veya `kaydedildi` ise beyaz `.sonuc-basari-card`
  (`#fff` zemin, `#555` sol kenarlık) içinde başarı rozeti gösterilir. Okunan PDF verisi
  `.veri-ozet` tablosunda özetlenir; kaydedilmediyse eksik alanlar listelenir.
- **`eslestirme.html`**: `GET /eslestirmeler/manuel` (bkz. `eslestirme_routes.manuel`)
  tarafından render edilir; `.eslestirme-grid` (3 sütunlu CSS grid: sol/orta/sağ). Sol
  sütunda bekleyen faturalar (`durum` odenmedi/kismi, radio `name="fatura_id"`), sağ
  sütunda henüz eşleştirilmemiş ödemeler (radio `name="odeme_id"`), ortada tutar `<input>`
  ve "Eşleştir" butonu. Ödeme seçilince tutar otomatik dolar; buton tıklanınca JS
  `fetch(POST /eslestirmeler/eslestir)` çağrılır (mevcut JSON API'yi kullanır, yeni endpoint
  eklenmedi), sonuç `.eslestirme-sonuc` kutusunda gösterilip sayfa yenilenir.
- **`musteriler/liste.html`**: `GET /musteriler/` tarafından render edilir; üstte arama
  kutusu (`GET ?q=`, ünvan/vergi_no üzerinde `ilike`), Aktif/Pasif/Hepsi filtre
  sekmeleri (`?filtre=`, varsayılan `aktif`) ve "Yeni Müşteri" butonu, altta
  `.data-table` (ünvan, vergi no, tür rozeti, e-posta, İşlemler: Düzenle linki +
  aktif müşteride pasife-al / pasif müşteride aktif-yap formu). Pasif müşteriler
  `.satir-pasif` sınıfıyla soluk gösterilir, liste aktif müşterileri üstte sıralar
  (`aktif` DESC, sonra `unvan`).
- **`musteriler/form.html`**: Yeni ve düzenle aynı şablonu kullanır (`musteri` ve
  `form_data` bağlamına göre alanlar doldurulur — doğrulama hatasında `form_data` ile
  girilen veriler korunur, GET'te `musteri` nesnesinden doldurulur). Zorunlu alanlar
  (`unvan`, `vergi_no`) HTML5 `required` ile işaretli, tarayıcı boşken submit'i engeller.
  Kaydet/İptal butonları `.form-actions` ile yan yana.
- **`base.html`**: `.content` bloğunun başına `get_flashed_messages(with_categories=true)`
  render eden bir `.flash-messages` bloğu eklendi — kategori `hata` koyu gri
  (`.flash-item.flash-hata`, `#333` metin/kenarlık), kategori `basari` açık gri zemin
  (`.flash-item.flash-basari`, `#f4f4f4` arka plan + `#ddd` kenarlık).
- **`main.css`**: Tüm stiller tek dosyada, inline style kullanılmaz. Yeni bölümler:
  sidebar/layout, `.dropzone`/`.file-info` (sürükle-bırak), `.sonuc-*`/`.badge-*`/`.veri-ozet`
  (doğrulama sonucu), `.eslestirme-grid`/`.secim-item`/`.eslestirme-orta` (manuel eşleştirme),
  `.tag` (müşteri türü rozeti), responsive `@media` bloğu. Palet değişmedi: yalnızca
  `#111 #333 #555 #888 #aaa #ddd #f4f4f4 #fff`.

## Veri Modeli Özeti

### Musteri (`musteriler`)
- `id`, `unvan` (String(200), zorunlu), `vergi_no` (String(20), unique + zorunlu),
  `vergi_dairesi`, `tur` (musteri/tedarikci/her_ikisi, varsayılan musteri), `iban`
  (String(50)), `email`, `telefon`, `adres` (Text), `aktif` (Boolean, varsayılan True —
  fiziksel silme yok, pasife alma ile yönetilir), `created_at` (DateTime, varsayılan
  `datetime.utcnow`)
- İlişkiler: `faturalar` (1-N Fatura), `odemeler` (1-N Odeme)

### Fatura (`faturalar`)
- `id`, `fatura_no` (unique), `fatura_tarihi`, `vade_tarihi`, `tur` (satis/alis),
  `net_tutar`, `kdv_orani`, `kdv_tutari`, `genel_toplam`, `para_birimi` (varsayılan TRY),
  `durum` (odenmedi/odendi/kismi), `aciklama`, `musteri_id` (FK → Musteri), `dosya_yolu`
- İlişkiler: `musteri` (backref), `eslestirmeler` (1-N Eslestirme)
- `genel_toplam = net_tutar + kdv_tutari` (kdv_tutari = net_tutar * kdv_orani / 100)

### Odeme (`odemeler`)
- `id`, `odeme_no`, `odeme_tarihi`, `tutar`, `yontem`, `banka_hesabi`, `referans_no`,
  `musteri_id` (FK → Musteri)
- İlişkiler: `musteri` (backref), `eslestirmeler` (1-N Eslestirme)

### HesapPlani (`hesap_plani`)
- `id`, `hesap_kodu` (unique), `hesap_adi`, `hesap_turu`, `borc`, `alacak`
- Bağımsız muhasebe hesap planı tablosu; Musteri/Fatura/Odeme ile doğrudan ilişkisi yok.

### Eslestirme (`eslestirmeler`)
- `id`, `odeme_id` (FK → Odeme), `fatura_id` (FK → Fatura), `eslestirilen_tutar`,
  `eslestirme_tarihi`, `kalan_bakiye`, `durum` (tam/kismi/bekliyor), `olusturan`
- Bir Fatura ve bir Odeme'yi birbirine bağlayan ilişki (kayıt) tablosudur; N-N ilişkiyi
  ara tablo üzerinden temsil eder (bir fatura birden çok ödemeyle kısmi eşleşebilir).

### İlişki Şeması
```
Musteri (1) ──< Fatura (N)
Musteri (1) ──< Odeme (N)
Fatura (1) ──< Eslestirme (N) >── (1) Odeme
HesapPlani  (bağımsız, muhasebe hesap kodları)
```

## PDF Fatura Yükleme Akışı

`services/pdf_service.py` içindeki `faturadan_veri_cikar(dosya_yolu)` fonksiyonu,
pdfplumber ile PDF metnini okuyup regex desenleriyle şu alanları çıkarır: `fatura_no`,
`fatura_tarihi`, `vade_tarihi`, `vergi_no`, `unvan`, `net_tutar`, `kdv_orani`,
`kdv_tutari`, `genel_toplam`. Tarihler `date` nesnesine, tutarlar `float`'a çevrilir
(TR biçimi "1.234,56" desteklenir). Bulunamayan her alan `None` olarak bırakılır ve
sonuç sözlüğündeki `eksik_alanlar` listesine eklenir.

`routes/fatura_routes.py` içindeki `POST /faturalar/yukle` endpoint'i:
1. `multipart/form-data` ile gelen `dosya` alanını okur, uzantının `.pdf` olduğunu
   doğrular (değilse 400 döner).
2. Dosyayı zaman damgalı, güvenli (secure_filename) bir adla `UPLOAD_FOLDER`
   (`config.py` → varsayılan `uploads/`) klasörüne kaydeder.
3. `faturadan_veri_cikar` ile veriyi çıkarır.
4. Zorunlu alanlardan (`fatura_no`, `net_tutar`, `genel_toplam`, form'dan gelen
   `musteri_id`) biri eksikse Fatura kaydedilmez; çıkarılan veri, eksik alan listesi
   ve kaydedilen dosya yolu JSON olarak döndürülür (kullanıcı formu tamamlayabilsin diye).
5. Tüm zorunlu alanlar mevcutsa, `dosya_yolu` alanı doldurulmuş yeni bir `Fatura`
   kaydı oluşturulup commit edilir ve oluşturulan kaydın bilgisi JSON olarak döner.

`config.py` içine `UPLOAD_FOLDER` eklendi; `app.py` uygulama başlarken bu klasörü
(varsa dokunmadan) otomatik oluşturur.

## Fatura Verisi Doğrulama Kuralları

`services/dogrulama_service.py` içindeki `pdf_verisini_dogrula(veri)` fonksiyonu,
PDF'den çıkarılan (veya JSON ile gönderilen) fatura verisini şu kurallara göre
kontrol eder:

**Zorunlu alanlar** (eksikse `hatalar` listesine `{"alan": ..., "mesaj": "Zorunlu
alan eksik"}` eklenir ve `durum = "hata"` olur): `fatura_no`, `fatura_tarihi`,
`vergi_no`, `unvan`, `genel_toplam`.

**Mantık kontrolleri** (yanlışsa `uyarilar` listesine eklenir, tüm zorunlu alanlar
mevcutsa `durum = "uyari"` olur):
- `net_tutar + kdv_tutari == genel_toplam` (±0.01 tolerans)
- `kdv_tutari == net_tutar * (kdv_orani / 100)` (±0.01 tolerans)
- `vade_tarihi >= fatura_tarihi`
- `genel_toplam > 0`

Hiçbir hata/uyarı yoksa `durum = "gecerli"`. Çıktı formatı:
`{"hatalar": [...], "uyarilar": [...], "durum": "gecerli"|"hata"|"uyari"}`.

`routes/fatura_routes.py` içine `POST /faturalar/dogrula` endpoint'i eklendi: JSON
body (veya form-data) ile gönderilen fatura alanlarını (`fatura_no`, `fatura_tarihi`
[`YYYY-MM-DD`], `vade_tarihi`, `vergi_no`, `unvan`, `net_tutar`, `kdv_orani`,
`kdv_tutari`, `genel_toplam`) `pdf_verisini_dogrula` ile kontrol edip sonucu JSON
olarak döner; dosya kaydetmez, veritabanına yazmaz (salt doğrulama).

## Müşteri (Cari) Modülü

`routes/musteri_routes.py` (`musteri_bp`, `url_prefix="/musteriler"`) müşteri
CRUD'unu (fiziksel silme hariç) sağlar:

- `_form_verisi(form)`: `request.form`'dan `unvan`/`vergi_no`'yu `strip()`'ler,
  opsiyonel alanları (`vergi_dairesi`, `iban`, `email`, `telefon`, `adres`) boşsa
  `None` yapar, `tur` için varsayılan `"musteri"` uygular.
- `_musteri_verisini_dogrula(veri, mevcut_id=None)`: sırasıyla kontrol eder —
  1. `unvan` boş → `"Ünvan zorunludur"`
  2. `vergi_no` boş → `"Vergi No zorunludur"`
  3. `vergi_no` başka bir kayıtta zaten varsa (düzenlemede kendi kaydı hariç
     tutulur, `mevcut_id` ile) → `"Bu vergi numarası zaten kayıtlı"`
  Hata yoksa `None` döner. Hata varsa route içinde `flash(hata, "hata")` ile
  gösterilir ve form, kullanıcının girdiği veriyle (`form_data`) tekrar render
  edilir — kullanıcı formu yeniden doldurmak zorunda kalmaz.
- Route'lar: `GET /` (`liste`, `?filtre=aktif|pasif|hepsi` — varsayılan `aktif` —
  ile birlikte `?q=` ile `unvan`/`vergi_no` üzerinde `ilike` araması, `aktif`
  DESC + `unvan` sıralı), `GET/POST /yeni` (`yeni`), `GET/POST /<id>/duzenle`
  (`duzenle`), `POST /<id>/sil` (`sil` — fiziksel silme yapmaz, sadece
  `aktif=False` yapıp `flash("...", "basari")` ile `filtre=aktif` listesine
  yönlendirir), `POST /<id>/aktif-yap` (`aktif_yap` — pasif müşteriyi tekrar
  `aktif=True` yapıp `filtre=pasif` listesine yönlendirir), `GET /ara` (`ara` —
  `?q=` ile arayıp JSON liste döner, arama kutusu/otomatik tamamlama gibi
  istemci taraflı kullanımlar için).
- Başarılı kayıt/güncelleme/pasife alma işlemlerinde `flash(..., "basari")`
  kullanılır; `templates/base.html` artık `.content` bloğunun başında
  `get_flashed_messages(with_categories=true)` render eden bir flash mesaj
  bloğu içerir (kategori `hata` → koyu gri, kategori `basari` → açık gri zemin +
  kenarlık, palet dışına çıkılmaz).
- `routes/fatura_routes.py` (`ekle`, `yukle_sayfa`) ve `routes/odeme_routes.py`
  (`ekle`) içindeki müşteri `<select>` dropdown'ları artık
  `Musteri.query.filter_by(aktif=True).order_by(Musteri.unvan).all()` kullanıyor
  (önceden `Musteri.query.all()` idi) — pasife alınan müşteriler yeni
  fatura/ödeme formlarında görünmez.
- Eski `templates/musteri_listesi.html` kaldırıldı; yerine `templates/musteriler/`
  klasörü altında `liste.html` ve `form.html` (yeni/düzenle ortak şablon) eklendi.

## Notlar
- `db` nesnesi döngüsel import'u önlemek için `models/__init__.py` içinde tanımlanır;
  tüm model dosyaları `from models import db` şeklinde import eder.
- Şablonlarda ve CSS'te sadece belirtilen gri tonlar kullanılmalıdır, renkli hiçbir
  öğe (arka plan, yazı rengi, kenarlık vb.) eklenmemelidir.

## Fatura-Ödeme Eşleştirme Mantığı

`Fatura` modelinde `kalan` adında salt-okunur bir `@property` bulunur (db kolonu
değildir): `genel_toplam - (faturaya bağlı tüm Eslestirme kayıtlarının
eslestirilen_tutar toplamı)`. Bu sayede kalan bakiye her zaman güncel eşleştirme
kayıtlarından türetilir, ayrı bir alanda tutulup senkron dışı kalma riski oluşmaz.

`services/eslestirme_service.py` içindeki fonksiyonlar:

- **`otomatik_eslestir(olusturan="sistem")`** (mevcut): Ödenmemiş faturaları, henüz
  kullanılmamış ödemelerle aynı müşteri + aynı tutar kuralına göre otomatik eşleştirir.
- **`manuel_eslestir(fatura_id, odeme_id, tutar, olusturan="kullanici")`** (mevcut):
  Basit manuel eşleştirme, doğrulama yapmadan kayıt oluşturur.
- **`eslestir(odeme_id, fatura_id, tutar, olusturan="kullanici")`** (yeni): Asıl
  doğrulamalı eşleştirme fonksiyonu.
  1. Ödeme ve faturayı `Query.get` ile çeker; biri yoksa
     `{"basarili": False, "hata": ...}` döner.
  2. Fatura `durum == "odendi"` ise (tam kapanmışsa) hata döner.
  3. `tutar > odeme.tutar` ise hata döner (bir ödeme, tutarından fazla eşleştirilemez).
  4. Yeni bir `Eslestirme` kaydı oluşturup `flush` eder, ardından faturaya ait TÜM
     `Eslestirme` kayıtlarının `eslestirilen_tutar` toplamını veritabanından
     yeniden hesaplar (`toplam_eslestirilen`).
  5. `kalan = fatura.genel_toplam - toplam_eslestirilen`. `kalan <= 0` ise
     `fatura.durum = "odendi"` ve yeni eşleştirmenin `durum`u `"tam"`; aksi halde
     `fatura.durum = "kismi"` ve eşleştirme `durum`u `"kismi"`. Eşleştirmenin
     `kalan_bakiye` alanına da bu değer yazılır.
  6. Commit edip `{"basarili": True, "eslestirme": ..., "kalan": ..., "fatura_durum": ...}`
     döner.
- **`bekleyen_faturalar(musteri_id)`** (yeni): Verilen müşteriye ait, `durum`u
  `"odenmedi"` veya `"kismi"` olan faturaları (tarihe göre azalan) listeler.
- **`eslestirme_ozeti(fatura_id)`** (yeni): Faturaya ait tüm `Eslestirme` kayıtlarını
  (tarihe göre artan), toplam eşleştirilen tutarı, kalan bakiyeyi ve faturanın
  güncel durumunu bir sözlük olarak döner; fatura bulunamazsa `None` döner.

`routes/eslestirme_routes.py` içine eklenen endpoint'ler:
- `POST /eslestirmeler/eslestir`: JSON veya form ile `odeme_id`, `fatura_id`, `tutar`
  alır, `eslestir` servisini çağırır; hata varsa 400, başarılıysa 201 ile
  `eslestirme_id`, `kalan`, `fatura_durum` döner.
- `GET /eslestirmeler/bekleyen/<musteri_id>`: `bekleyen_faturalar` sonucunu JSON
  liste olarak döner (`id`, `fatura_no`, `genel_toplam`, `kalan`, `durum`).
- `GET /eslestirmeler/ozet/<fatura_id>`: `eslestirme_ozeti` sonucunu JSON olarak
  döner; fatura yoksa 404.

## Endpoint Listesi

| Yol | Metot | Açıklama |
| --- | --- | --- |
| `/` | GET | Anasayfa (`index.html`) |
| `/faturalar/` | GET | Fatura listesini gösterir |
| `/faturalar/ekle` | GET, POST | Manuel fatura ekleme formu (form alanlarıyla, `fatura_verisini_dogrula` kullanır) |
| `/faturalar/yukle` | POST | PDF yükleme JSON API'si; dosyayı kaydeder, veri çıkarır, zorunlu alanlar tamsa `Fatura` oluşturur |
| `/faturalar/yukle-sayfa` | GET, POST | PDF yükleme sayfası (dropzone formu); POST'ta `_pdf_dosyasini_kaydet_ve_isle` + `pdf_verisini_dogrula` çalıştırıp `dogrulama_sonuc.html` render eder |
| `/faturalar/dogrula` | POST | JSON/form ile gönderilen fatura alanlarını `pdf_verisini_dogrula` ile kontrol eder; kaydetmez, salt doğrulama sonucu JSON döner |
| `/odemeler/` | GET | Ödeme listesini gösterir |
| `/odemeler/ekle` | GET, POST | Manuel ödeme ekleme formu (`odeme_verisini_dogrula` kullanır) |
| `/eslestirmeler/` | GET | Tüm `Eslestirme` kayıtlarının geçmiş listesi |
| `/eslestirmeler/manuel` | GET | Manuel eşleştirme ekranı (bekleyen faturalar + eşleşmemiş ödemeler) |
| `/eslestirmeler/otomatik-calistir` | POST | `otomatik_eslestir()` servisini çalıştırıp listeye yönlendirir |
| `/eslestirmeler/eslestir` | POST | JSON/form ile `odeme_id`, `fatura_id`, `tutar` alır, `eslestir()` servisini çağırır (201 başarı / 400 hata) |
| `/eslestirmeler/bekleyen/<int:musteri_id>` | GET | Müşteriye ait bekleyen (ödenmedi/kısmi) faturaları JSON liste olarak döner |
| `/eslestirmeler/ozet/<int:fatura_id>` | GET | Faturanın eşleştirme özetini (toplam eşleştirilen, kalan, durum, eşleştirme listesi) JSON olarak döner |
| `/musteriler/` | GET | Müşteri listesini `?filtre=aktif\|pasif\|hepsi` (varsayılan `aktif`) ve `?q=` ile ünvan/vergi_no aramasıyla gösterir |
| `/musteriler/yeni` | GET, POST | Yeni müşteri formu; POST'ta doğrulayıp kaydeder, hata varsa formu (girilen verilerle) tekrar gösterir |
| `/musteriler/<int:musteri_id>/duzenle` | GET, POST | Dolu form; POST'ta günceller, hata varsa formu (girilen verilerle) tekrar gösterir |
| `/musteriler/<int:musteri_id>/sil` | POST | Fiziksel silme yapmaz, `aktif=False` yapar (pasife alır), `filtre=aktif` listesine yönlendirir |
| `/musteriler/<int:musteri_id>/aktif-yap` | POST | Pasif müşteriyi `aktif=True` yapar, `filtre=pasif` listesine yönlendirir |
| `/musteriler/ara` | GET | `?q=` (min 2 karakter) ve `?filtre=aktif\|pasif\|hepsi` ile ünvan/vergi_no üzerinde `ilike` araması yapar, en fazla 20 sonucu (`id`, `unvan`, `vergi_no`, `tur`, `email`, `aktif`) JSON liste olarak döner |

## Bilinen Kısıtlar ve Sonraki Adımlar

- Kimlik doğrulama / yetkilendirme (login, rol bazlı erişim) yok — tüm route'lar açık.
- `otomatik_eslestir()` yalnızca manuel tetiklenir (`POST /eslestirmeler/otomatik-calistir`);
  zamanlanmış görev (cron/scheduler) yok.
- Oluşturulan `Eslestirme` kayıtları için silme/geri alma (undo) endpoint'i yok.
- Liste sayfalarında (fatura/ödeme/eşleştirme) sayfalama (pagination) yok, tüm kayıtlar
  tek seferde çekiliyor.
- Yüklenen PDF dosyaları `UPLOAD_FOLDER` (`uploads/`) altında birikir, otomatik
  temizleme/arşivleme mekanizması yok.
- `HesapPlani` modeli tanımlı ama henüz hiçbir route/servis/şablon tarafından
  kullanılmıyor (bağımsız, ileride genel muhasebe hesap eşleştirmesi için ayrılmış).
- Otomatik test paketi (pytest/CI) repoda yok; uçtan uca akış bu oturumda geçici bir
  `test_akis_gecici.py` betiğiyle (Flask `test_client`, sahte PDF, ayrı test DB'si)
  manuel olarak doğrulanıp iş bitince silindi.
- `pdf_service` regex tabanlı çıkarım yaptığından, faturanın PDF şablonu (etiket
  isimleri, biçimi) `_DESENLER` içindeki desenlerden belirgin şekilde farklıysa alanlar
  `None`/eksik kalabilir.

## Güncelleme Günlüğü
- **2026-09-17**: İlk proje iskeleti oluşturuldu (app.py, config.py, requirements.txt,
  models/, routes/, services/, templates/, static/). Musteri/Hesap/Fatura/Odeme/Eslestirme
  modelleri, ilgili blueprint'ler, doğrulama ve eşleştirme servisleri ile gri tonlu
  temel arayüz şablonları eklendi.
- **2026-09-17**: Modeller SQLAlchemy ile nihai şemaya güncellendi: Musteri (unvan,
  vergi_no, vergi_dairesi, tur, iban, email), Fatura (fatura_no, fatura_tarihi,
  vade_tarihi, tur, net_tutar, kdv_orani, kdv_tutari, genel_toplam, para_birimi,
  durum, aciklama, musteri_id, dosya_yolu), Odeme (odeme_no, odeme_tarihi, tutar,
  yontem, banka_hesabi, referans_no, musteri_id), HesapPlani (hesap_kodu, hesap_adi,
  hesap_turu, borc, alacak) — eski Hesap modelinin yerine geçti, Eslestirme
  (odeme_id, fatura_id, eslestirilen_tutar, eslestirme_tarihi, kalan_bakiye, durum,
  olusturan). Bağımlı routes/ ve templates/ dosyaları yeni alan adlarına göre
  güncellendi; eşleştirme servisi kalan_bakiye/durum mantığına uyarlandı. app.py
  içindeki db.create_all() değişmedi, yeni şemayla tabloları otomatik oluşturur.
- **2026-09-17**: `services/pdf_service.py` tamamlandı — pdfplumber ile PDF metni
  okunup regex tabanlı alan çıkarma eklendi (fatura_no, fatura_tarihi, vade_tarihi,
  vergi_no, unvan, net_tutar, kdv_orani, kdv_tutari, genel_toplam); bulunamayan
  alanlar `None` + `eksik_alanlar` listesiyle işaretleniyor. `routes/fatura_routes.py`
  içine `POST /faturalar/yukle` endpoint'i eklendi: sadece `.pdf` kabul eder, dosyayı
  `UPLOAD_FOLDER`'a kaydeder, pdf_service ile veri çıkarır, zorunlu alanlar tamsa
  `Fatura` kaydını `dosya_yolu` ile birlikte oluşturur, eksikse kaydetmeden veriyi
  JSON olarak döner. `config.py`'ye `UPLOAD_FOLDER` eklendi, `app.py` açılışta bu
  klasörü otomatik oluşturuyor.
- **2026-09-17**: `services/dogrulama_service.py` içine `pdf_verisini_dogrula(veri)`
  eklendi — zorunlu alanları (`fatura_no`, `fatura_tarihi`, `vergi_no`, `unvan`,
  `genel_toplam`) ve mantık kurallarını (net+kdv=genel_toplam, kdv_tutari=net*oran/100,
  vade_tarihi>=fatura_tarihi, genel_toplam>0, ±0.01 tolerans) kontrol edip
  `{"hatalar": [...], "uyarilar": [...], "durum": "gecerli"|"hata"|"uyari"}` döner.
  Mevcut `fatura_verisini_dogrula`/`odeme_verisini_dogrula` fonksiyonlarına
  dokunulmadı. `routes/fatura_routes.py` içine `POST /faturalar/dogrula` endpoint'i
  eklendi (JSON/form ile fatura alanlarını alır, kaydetmeden doğrulama sonucunu
  JSON olarak döner).
- **2026-09-17**: `services/eslestirme_service.py` içine doğrulamalı `eslestir`,
  `bekleyen_faturalar` ve `eslestirme_ozeti` fonksiyonları eklendi (mevcut
  `otomatik_eslestir`/`manuel_eslestir`'e dokunulmadı). `models/fatura.py` içine
  `kalan` adında salt-okunur `@property` eklendi (genel_toplam - eşleştirilen
  toplam). `routes/eslestirme_routes.py` içine `POST /eslestirmeler/eslestir`,
  `GET /eslestirmeler/bekleyen/<musteri_id>` ve `GET /eslestirmeler/ozet/<fatura_id>`
  endpoint'leri eklendi.
- **2026-09-17**: Arayüz gri-ton tasarımı tamamlandı. `templates/base.html` sidebar
  navigasyonlu layout'a geçirildi (`.app-layout` / `.sidebar` / `.main-area` /
  `.content`); eski `.site-header`/`.container` tabanlı üst menü kaldırıldı.
  `static/css/main.css` tamamen bu düzene göre güncellendi (sidebar, dropzone,
  doğrulama sonucu rozetleri/kartları, eşleştirme grid'i, responsive breakpoint);
  hâlâ yalnızca belirtilen gri tonlar kullanılıyor, inline style yok. Dört yeni
  şablon eklendi: `fatura_yukle.html` (PDF sürükle-bırak yükleme formu),
  `dogrulama_sonuc.html` (hata=koyu gri, uyarı=açık gri, başarı=beyaz kart),
  `eslestirme.html` (sol bekleyen faturalar / sağ ödemeler / ortada eşleştir
  butonu — mevcut `POST /eslestirmeler/eslestir` JSON API'sini `fetch` ile çağırır),
  `musteri_listesi.html` (müşteri tablosu). Bunları beslemek için üç yeni sayfa
  route'u eklendi: `routes/fatura_routes.py` içine `GET/POST /faturalar/yukle-sayfa`
  (`yukle_sayfa`, PDF işleme mantığı mevcut `/faturalar/yukle` JSON endpoint'iyle
  ortak `_pdf_dosyasini_kaydet_ve_isle` yardımcı fonksiyonunda birleştirildi — JSON
  API davranışı değişmedi), `routes/eslestirme_routes.py` içine `GET
  /eslestirmeler/manuel` (`manuel`), ve yeni `routes/musteri_routes.py` blueprint'i
  (`GET /musteriler/` → `liste`), `app.py` içine kaydedildi. Tüm sayfa route'ları
  (`/`, `/faturalar/`, `/faturalar/yukle-sayfa`, `/odemeler/`, `/eslestirmeler/`,
  `/eslestirmeler/manuel`, `/musteriler/`) manuel olarak test edilip 200 döndüğü
  doğrulandı.
- **2026-09-17**: Uygulama uçtan uca ayağa kaldırılıp doğrulandı. `app.py` içinde
  dört blueprint (`fatura_bp`, `odeme_bp`, `eslestirme_bp`, `musteri_bp`) zaten
  kayıtlıydı; `.venv` oluşturulup `requirements.txt` (`Flask`, `Flask-SQLAlchemy`,
  `pdfplumber`, `Werkzeug`, `python-dotenv`) kurulup `python app.py` ile açılışta
  hata vermediği ve `app.url_map`'in tüm route'ları içerdiği doğrulandı.
  Tüm akış (a→f) Flask `test_client` ile uçtan uca test edildi (geçici
  `test_akis_gecici.py`, ayrı test DB'si `test_akis.db` ve sahte PDF ile, iş
  bitince ikisi de silindi): (a) sahte fatura PDF'i `POST /faturalar/yukle-sayfa`
  ile yüklendi → 200 ve `Fatura` kaydı oluştu; (b) aynı veriler `POST
  /faturalar/dogrula` ile gönderildi → `durum: "gecerli"`; (c) fatura veritabanına
  zaten (a) adımında yazıldığı doğrulandı; (d) `POST /odemeler/ekle` ile aynı
  müşteriye, faturanın `genel_toplam`ına eşit tutarda `Odeme` eklendi (302
  yönlendirme); (e) `POST /eslestirmeler/eslestir` ile ödeme-fatura eşleştirildi →
  201, `fatura_durum: "odendi"`, `kalan: 0.0`; (f) `GET
  /eslestirmeler/ozet/<fatura_id>` ile özet alındı → `durum: "odendi"`, eşleştirme
  kaydı listelendi. Ayrıca yedi sayfa route'unun (`/`, `/faturalar/`,
  `/faturalar/yukle-sayfa`, `/odemeler/`, `/eslestirmeler/`,
  `/eslestirmeler/manuel`, `/musteriler/`) hepsinin 200 döndüğü tekrar doğrulandı.
  `requirements.txt`'e eksik olan `Werkzeug==3.0.3` satırı eklendi (Flask'ın zaten
  bağımlılığı olarak kuruluydu, ama açıkça listelendi). context.md'ye "Endpoint
  Listesi" (tüm yol/metot/açıklama tablosu) ve "Bilinen Kısıtlar ve Sonraki
  Adımlar" bölümleri eklendi.
- **2026-09-17**: Müşteri (cari) yönetimi modülü tamamlandı. `models/musteri.py`
  şemaya `telefon`, `adres` (Text), `aktif` (Boolean, varsayılan True) ve
  `created_at` (DateTime) eklendi; `unvan` `String(200)`'e, `iban` `String(50)`'ye
  genişletildi, `vergi_no` artık `nullable=False`. `routes/musteri_routes.py`
  tamamen yeniden yazıldı: `GET /` (liste, `?q=` arama + aktif önce sıralama),
  `GET/POST /yeni`, `GET/POST /<id>/duzenle`, `POST /<id>/sil` (fiziksel silme
  yok, `aktif=False`), `GET /ara` (JSON arama). Doğrulama (`unvan`/`vergi_no`
  zorunlu, `vergi_no` tekilliği) `flash()` ile gösteriliyor, form verileri
  hatada korunuyor. `templates/base.html` içine `get_flashed_messages` render
  eden flash mesaj bloğu eklendi (`.flash-item.flash-hata` / `.flash-basari`,
  palet dışına çıkılmadı). Eski `musteri_listesi.html` silinip yerine
  `templates/musteriler/liste.html` ve `templates/musteriler/form.html`
  (yeni/düzenle ortak) eklendi; `main.css`'e `.flash-messages`, `.search-form`,
  `.form-actions`, `.inline-form`, `.btn-small`, `.islem-hucresi`, `.satir-pasif`
  sınıfları eklendi. `routes/fatura_routes.py` (`ekle`, `yukle_sayfa`) ve
  `routes/odeme_routes.py` (`ekle`) içindeki müşteri dropdown'ları
  `Musteri.query.filter_by(aktif=True).order_by(Musteri.unvan).all()` kullanacak
  şekilde güncellendi. Şema değiştiği için eski `muhasebe.db` silindi (bir sonraki
  çalıştırmada `db.create_all()` ile otomatik yeniden oluşur). Yeni akış (yeni
  müşteri ekleme, eksik alan hatası, tekil vergi_no hatası, listeleme, arama,
  düzenleme, pasife alma, pasif müşterinin fatura formunda görünmemesi) Flask
  `test_client` ile uçtan uca doğrulandı, test verisi/`muhasebe.db` sonra
  temizlendi. context.md'ye "Müşteri (Cari) Modülü" bölümü, model/endpoint/klasör
  yapısı güncellemeleri ve bu günlük maddesi eklendi.
- **2026-09-17 (gerçekçi test verisiyle uçtan uca doğrulama)**: `muhasebe.db`
  içine kalıcı test verisi eklendi — bu kez geçici ayrı bir test DB'si yerine
  gerçek veritabanı kullanıldı ve veriler **silinmeden** bırakıldı (uygulamayı
  tarayıcıda dolu haliyle incelemek için). Geçici `seed_test_data_gecici.py`
  betiği (iş bitince silindi) ile: 20 farklı Türkiye merkezli firma adıyla
  `Musteri` kaydı oluşturuldu (18'i `aktif=True`, 2'si `aktif=False`; `tur`
  dağılımı musteri/tedarikci/her_ikisi karışık; her biri tekil `vergi_no`,
  `iban`, `email`, `telefon`, `adres` ile dolduruldu). Her müşteriye 1 `Fatura`
  (toplam 20, artan tutarlarla, `kdv_orani=20`) ve 18 müşteriye `Odeme`
  eklendi: 14'ü faturanın `genel_toplam`ına **birebir eşit** tutarda (otomatik
  tam eşleşme senaryosu), 4'ü faturanın **yarısı** kadar (kısmi ödeme
  senaryosu), 2 pasif müşteriye hiç ödeme eklenmedi (bekleyen fatura senaryosu).
  Sonuçlar:
  - `otomatik_eslestir()` çalıştırıldığında 14 `Eslestirme` kaydı oluştu, ilgili
    14 fatura `durum="odendi"` oldu; kalan 6 fatura `"odenmedi"` durumunda kaldı
    (4 kısmi ödemeli + 2 ödemesiz) — **doğrulanan davranış**: otomatik eşleştirme
    yalnızca `fatura.genel_toplam == odeme.tutar` birebir eşitliğinde çalışıyor,
    kısmi tutarları kendiliğinden eşleştirmiyor (beklenen/doğru davranış, bug
    değil).
  - Kısmi ödemelerden biri için doğrulamalı `eslestir(odeme_id, fatura_id, tutar)`
    servisi elle çağrılarak test edildi: `{"basarili": true, "kalan": 1755.0,
    "fatura_durum": "kismi"}` döndü ve fatura `durum`u `"kismi"`, `kalan`
    property'si doğru hesaplandı (3510.0 → 1755.0) — kısmi eşleştirme mantığı
    da doğru çalışıyor.
  - `Flask test_client` ile sekiz sayfa/endpoint (`/`, `/musteriler/`,
    `/musteriler/?q=Anadolu`, `/faturalar/`, `/odemeler/`, `/eslestirmeler/`,
    `/eslestirmeler/manuel`, `/musteriler/ara?q=tekstil`) 200 döndü;
    `/eslestirmeler/bekleyen/<musteri_id>` ve `/eslestirmeler/ozet/<fatura_id>`
    JSON endpoint'leri de doğru veriyle 200 döndürdü.
  - **Sonuç**: Sistem 20 müşteri / 20 fatura / 18 ödeme / 15 eşleştirme kaydıyla
    (14 otomatik tam + 1 manuel kısmi) beklendiği gibi çalışıyor; müşteri
    listesi arama, aktif/pasif ayrımı, fatura-ödeme otomatik ve manuel
    eşleştirme akışlarının tümü gerçekçi veriyle doğrulandı. `muhasebe.db`
    içindeki bu veriler bilinçli olarak silinmedi, tarayıcıdan (`python app.py`
    ile) incelenebilir durumda bırakıldı.
- **2026-09-17 (müşteri listesi buton hizası düzeltmesi)**: `templates/musteriler/liste.html`
  içindeki "Düzenle" linki ve "Pasife al" butonu farklı boyutlarda görünüp hizasız
  duruyordu (`.btn.btn-secondary.btn-small` CSS sınıfları `<a>` ve `<button>` için
  farklı render oluyordu). `.islem-hucresi` hücresi içine `display: flex; gap: 8px;
  align-items: center;` stilli bir `<div>` sarmalayıcı eklendi; her iki öğeye de
  eşit inline stil verildi (`width: 80px`, `padding: 6px 0`, `text-align: center`,
  `background-color: #ddd`, `color: #333`, `border: 1px solid #aaa`,
  `border-radius: 4px`, `font-size: 13px`) — artık ikisi de aynı boyutta ve yan
  yana hizalı. Mevcut `{% if musteri.aktif %}` / pasif için `"Pasif"` etiketi
  gösterme mantığına ve `url_for('musteri.duzenle'/'musteri.sil', musteri_id=...)`
  çağrılarına dokunulmadı; renk paleti (`#ddd`/`#aaa`/`#333`) korundu, başka
  hiçbir öğe değiştirilmedi.
- **2026-09-17 (pasif müşterileri aktif hale getirme)**: `routes/musteri_routes.py`
  içindeki `GET /` (`liste`) route'una `?filtre=aktif|pasif|hepsi` parametresi
  eklendi (varsayılan `aktif`); mevcut `?q=` arama filtresiyle birlikte çalışır.
  Yeni `POST /<musteri_id>/aktif-yap` (`aktif_yap`) route'u eklendi — müşteriyi
  `aktif=True` yapıp `flash(..., "basari")` ile `filtre=pasif` listesine
  yönlendirir. `sil` route'u artık işlem sonrası `filtre=aktif` listesine
  yönlendiriyor. `templates/musteriler/liste.html`'e tablonun üstüne gri tonlu
  (`#333`/`#f4f4f4`) Aktif/Pasif/Hepsi filtre sekmeleri eklendi; İşlemler
  hücresindeki buton bloğu `{% if musteri.aktif %}` ise "Pasife al" (`#ddd`),
  değilse "Aktif yap" (`#555`/`#fff`) butonunu gösterecek şekilde güncellendi.
  Mevcut arama, satır hizası ve `.satir-pasif` soluklaştırma mantığına
  dokunulmadı, renk paleti dışına çıkılmadı.
- **2026-09-17 (anlık müşteri arama — LIKE/ilike, debounce, vurgulama)**:
  `routes/musteri_routes.py` içindeki `GET /ara` (`ara`) endpoint'i güçlendirildi:
  artık `?filtre=aktif|pasif|hepsi` parametresini de destekliyor (liste
  route'undaki filtre mantığıyla tutarlı), `q` 2 karakterden kısaysa boş JSON
  liste (`[]`) döner, sonuçlar `unvan`'a göre sıralanıp `limit(20)` ile
  sınırlanır, JSON çıktısına `email` alanı da eklendi (`id`, `unvan`,
  `vergi_no`, `tur`, `email`, `aktif`). Arama mantığı değişmedi: `db.or_(
  Musteri.unvan.ilike(f"%{q}%"), Musteri.vergi_no.ilike(f"%{q}%"))` (SQLite'ta
  `ilike` zaten `LIKE` ile aynı, büyük/küçük harf duyarsız). `templates/
  musteriler/liste.html` içindeki eski GET tabanlı `.search-form` kaldırılıp
  yerine `id="arama-input"` metin kutusu + `id="arama-durum"` durum etiketi
  (gri paletle, inline style) eklendi; `oninput="aramaYap(this.value)"` ile
  istemci tarafı canlı arama tetikleniyor. `<tbody>`'ye `id="musteri-tbody"`,
  her `<tr>`'ye `data-id="{{ musteri.id }}"` eklendi (mevcut `.satir-pasif`
  sınıfı ve İşlemler hücresindeki Düzenle/Pasife-al/Aktif-yap buton bloğuna
  dokunulmadı). Sayfanın sonuna (content bloğunun bitiminde) yeni bir
  `<script>` eklendi: `aramaYap()` fonksiyonu 300ms debounce ile
  `fetch('/musteriler/ara?q=...&filtre=...')` çağırır (mevcut sayfanın
  `filtre` bağlamı JS'e `const filtreDeger = "{{ filtre }}"` ile aktarılır),
  sonuçları `tbody.innerHTML` olarak render eder (`vurgula()` yardımcı
  fonksiyonu eşleşen metni `<strong style="color:#111;">` ile vurgular), 0
  sonuçta "sonuç bulunamadı" satırı gösterir, giriş temizlenince sayfa
  yüklenirkenki orijinal `tbody` içeriğini (`orijinalHTML`) geri yükler.
  Sadece 2 harften kısa girişte "En az 2 karakter gir" uyarısı gösterilir.
  Palet dışına çıkılmadı, filtre sekmeleri ve diğer davranışlara dokunulmadı.
  `.venv` + mevcut `muhasebe.db` (20 müşteri test verisi) ile `test_client`
  üzerinden `GET /musteriler/ara?q=ana&filtre=aktif` ve `GET /musteriler/`
  200 döndüğü ve doğru sonuçları içerdiği doğrulandı.

