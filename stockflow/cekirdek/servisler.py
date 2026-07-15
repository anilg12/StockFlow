# -*- coding: utf-8 -*-
# StockFlow · is mantigi katmani
# Arayuz burayi cagirir, veritabanina dogrudan dokunmaz.
# Anıl Gül · 2025

from datetime import datetime

from . import veritabani as db
from .yardimcilar import ay_etiketi, bugun, gun_ekle, icerir, simdi, son_aylar


class IsKurali(Exception):
    """Kullaniciya gosterilecek dogrulama hatasi."""


# --- kategoriler ----------------------------------------------------------

def kategoriler():
    return db.sorgu("SELECT * FROM kategoriler ORDER BY ad COLLATE NOCASE")


def kategori_adlari():
    return [k["ad"] for k in kategoriler()]


def kategori_bul_yada_ac(ad):
    ad = (ad or "").strip()
    if not ad:
        return None
    satir = db.tek("SELECT id FROM kategoriler WHERE ad = ?", (ad,))
    if satir:
        return satir["id"]
    return db.ekle("kategoriler", {"ad": ad})


# --- urunler --------------------------------------------------------------

URUN_SORGU = """
SELECT u.*, COALESCE(k.ad, 'Kategorisiz') AS kategori
FROM urunler u LEFT JOIN kategoriler k ON k.id = u.kategori_id
"""


def urunler(arama="", kategori=None, sadece_kritik=False, sadece_aktif=False):
    satirlar = db.sorgu(URUN_SORGU + " ORDER BY u.ad COLLATE NOCASE")
    sonuc = []
    for s in satirlar:
        if sadece_aktif and not s["aktif"]:
            continue
        if kategori and kategori != "Tümü" and s["kategori"] != kategori:
            continue
        if sadece_kritik and s["stok"] > s["kritik_seviye"]:
            continue
        if arama:
            havuz = " ".join(str(s[k] or "") for k in ("kod", "ad", "barkod", "kategori"))
            if not icerir(havuz, arama):
                continue
        sonuc.append(s)
    return sonuc


def urun(urun_id):
    return db.tek(URUN_SORGU + " WHERE u.id = ?", (urun_id,))


def urun_kodu_uret():
    son = db.deger("SELECT COUNT(*) FROM urunler")
    while True:
        aday = "URN-{:04d}".format(son + 1)
        if db.tek("SELECT 1 FROM urunler WHERE kod = ?", (aday,)) is None:
            return aday
        son += 1


def urun_kaydet(veri, urun_id=None):
    ad = (veri.get("ad") or "").strip()
    kod = (veri.get("kod") or "").strip()
    if not ad:
        raise IsKurali("Ürün adı boş bırakılamaz.")
    if not kod:
        raise IsKurali("Ürün kodu boş bırakılamaz.")
    if veri.get("satis_fiyati", 0) < 0 or veri.get("alis_fiyati", 0) < 0:
        raise IsKurali("Fiyat negatif olamaz.")

    cakisma = db.tek("SELECT id FROM urunler WHERE kod = ?", (kod,))
    if cakisma and cakisma["id"] != urun_id:
        raise IsKurali("'{}' kodu başka bir üründe kullanılıyor.".format(kod))

    kayit = {
        "kod": kod,
        "ad": ad,
        "kategori_id": kategori_bul_yada_ac(veri.get("kategori")),
        "birim": veri.get("birim") or "Adet",
        "alis_fiyati": float(veri.get("alis_fiyati") or 0),
        "satis_fiyati": float(veri.get("satis_fiyati") or 0),
        "kritik_seviye": float(veri.get("kritik_seviye") or 0),
        "barkod": (veri.get("barkod") or "").strip(),
        "aciklama": (veri.get("aciklama") or "").strip(),
        "aktif": 1 if veri.get("aktif", True) else 0,
    }

    if urun_id:
        eski = db.tek("SELECT stok FROM urunler WHERE id = ?", (urun_id,))
        yeni_stok = float(veri.get("stok") or 0)
        db.guncelle("urunler", urun_id, kayit)
        if abs(yeni_stok - eski["stok"]) > 0.0001:
            stok_hareketi(urun_id, "Düzeltme", yeni_stok - eski["stok"], "Ürün kartından düzeltildi")
        return urun_id

    kayit["stok"] = 0
    kayit["olusturma"] = simdi()
    yeni_id = db.ekle("urunler", kayit)
    baslangic = float(veri.get("stok") or 0)
    if baslangic:
        stok_hareketi(yeni_id, "Giriş", baslangic, "Açılış stoğu")
    return yeni_id


def urun_sil(urun_id):
    kullanim = db.deger("SELECT COUNT(*) FROM satis_kalemleri WHERE urun_id = ?", (urun_id,))
    db.sil("urunler", urun_id)
    return kullanim


def stok_hareketi(urun_id, tip, miktar, aciklama=""):
    """miktar pozitif = giris, negatif = cikis. Stok kolonunu tek yerden guncelliyorum."""
    kayit = db.tek("SELECT stok, ad FROM urunler WHERE id = ?", (urun_id,))
    if kayit is None:
        raise IsKurali("Ürün bulunamadı.")
    onceki = float(kayit["stok"])
    sonraki = onceki + float(miktar)
    if sonraki < 0:
        raise IsKurali("'{}' için stok eksiye düşemez. Mevcut: {:g}".format(kayit["ad"], onceki))
    # Stok kolonu ile hareket kaydi birbirinden ayri dusemez, ikisi tek parca.
    with db.islem():
        db.calistir("UPDATE urunler SET stok = ? WHERE id = ?", (sonraki, urun_id))
        db.ekle("stok_hareketleri", {
            "urun_id": urun_id,
            "tip": tip,
            "miktar": float(miktar),
            "onceki": onceki,
            "sonraki": sonraki,
            "aciklama": aciklama,
            "tarih": simdi(),
        })
    return sonraki


def urun_hareketleri(urun_id, limit=100):
    return db.sorgu(
        "SELECT * FROM stok_hareketleri WHERE urun_id = ? ORDER BY id DESC LIMIT ?",
        (urun_id, limit),
    )


def kritik_urunler():
    return db.sorgu(
        URUN_SORGU + " WHERE u.aktif = 1 AND u.stok <= u.kritik_seviye ORDER BY (u.stok - u.kritik_seviye)"
    )


def stok_degeri():
    alis = db.deger("SELECT SUM(stok * alis_fiyati) FROM urunler WHERE aktif = 1", varsayilan=0)
    satis = db.deger("SELECT SUM(stok * satis_fiyati) FROM urunler WHERE aktif = 1", varsayilan=0)
    return float(alis or 0), float(satis or 0)


# --- musteriler -----------------------------------------------------------

def musteriler(arama="", tip=None, sadece_aktif=False):
    satirlar = db.sorgu("SELECT * FROM musteriler ORDER BY unvan COLLATE NOCASE")
    sonuc = []
    for s in satirlar:
        if sadece_aktif and not s["aktif"]:
            continue
        if tip and tip != "Tümü" and s["tip"] != tip:
            continue
        if arama:
            havuz = " ".join(str(s[k] or "") for k in ("kod", "unvan", "yetkili", "telefon", "eposta", "sehir"))
            if not icerir(havuz, arama):
                continue
        sonuc.append(s)
    return sonuc


def musteri(musteri_id):
    return db.tek("SELECT * FROM musteriler WHERE id = ?", (musteri_id,))


def musteri_kodu_uret():
    son = db.deger("SELECT COUNT(*) FROM musteriler")
    while True:
        aday = "MUS-{:04d}".format(son + 1)
        if db.tek("SELECT 1 FROM musteriler WHERE kod = ?", (aday,)) is None:
            return aday
        son += 1


def musteri_kaydet(veri, musteri_id=None):
    unvan = (veri.get("unvan") or "").strip()
    kod = (veri.get("kod") or "").strip()
    if not unvan:
        raise IsKurali("Müşteri ünvanı boş bırakılamaz.")
    if not kod:
        raise IsKurali("Müşteri kodu boş bırakılamaz.")

    cakisma = db.tek("SELECT id FROM musteriler WHERE kod = ?", (kod,))
    if cakisma and cakisma["id"] != musteri_id:
        raise IsKurali("'{}' kodu başka bir müşteride kullanılıyor.".format(kod))

    kayit = {
        "kod": kod,
        "unvan": unvan,
        "tip": veri.get("tip") or "Bireysel",
        "yetkili": (veri.get("yetkili") or "").strip(),
        "telefon": (veri.get("telefon") or "").strip(),
        "eposta": (veri.get("eposta") or "").strip(),
        "sehir": (veri.get("sehir") or "").strip(),
        "adres": (veri.get("adres") or "").strip(),
        "vergi_no": (veri.get("vergi_no") or "").strip(),
        "notlar": (veri.get("notlar") or "").strip(),
        "aktif": 1 if veri.get("aktif", True) else 0,
    }
    if musteri_id:
        db.guncelle("musteriler", musteri_id, kayit)
        return musteri_id
    kayit["bakiye"] = float(veri.get("bakiye") or 0)
    kayit["olusturma"] = simdi()
    return db.ekle("musteriler", kayit)


def musteri_sil(musteri_id):
    satis_adedi = db.deger("SELECT COUNT(*) FROM satislar WHERE musteri_id = ?", (musteri_id,))
    db.sil("musteriler", musteri_id)
    return satis_adedi


def musteri_ozeti(musteri_id):
    satir = db.tek(
        "SELECT COUNT(*) AS adet, COALESCE(SUM(toplam), 0) AS ciro, MAX(tarih) AS son "
        "FROM satislar WHERE musteri_id = ?",
        (musteri_id,),
    )
    gorusme = db.deger("SELECT COUNT(*) FROM gorusmeler WHERE musteri_id = ?", (musteri_id,))
    return {
        "adet": satir["adet"],
        "ciro": float(satir["ciro"] or 0),
        "son_satis": satir["son"],
        "ortalama": float(satir["ciro"] or 0) / satir["adet"] if satir["adet"] else 0.0,
        "gorusme": gorusme,
    }


def musteri_satislari(musteri_id):
    return db.sorgu("SELECT * FROM satislar WHERE musteri_id = ? ORDER BY tarih DESC, id DESC", (musteri_id,))


def bakiye_ekle(musteri_id, tutar):
    if not musteri_id:
        return
    db.calistir("UPDATE musteriler SET bakiye = bakiye + ? WHERE id = ?", (float(tutar), musteri_id))


# --- gorusmeler (CRM) -----------------------------------------------------

GORUSME_TIPLERI = ["Telefon", "E-posta", "Ziyaret", "Toplantı", "Teklif", "Şikayet"]


def gorusmeler(musteri_id):
    return db.sorgu(
        "SELECT * FROM gorusmeler WHERE musteri_id = ? ORDER BY tarih DESC, id DESC", (musteri_id,)
    )


def gorusme_kaydet(veri, gorusme_id=None):
    if not veri.get("konu", "").strip():
        raise IsKurali("Görüşme konusu boş bırakılamaz.")
    kayit = {
        "musteri_id": veri["musteri_id"],
        "tarih": veri.get("tarih") or bugun(),
        "tip": veri.get("tip") or "Telefon",
        "konu": veri["konu"].strip(),
        "notlar": (veri.get("notlar") or "").strip(),
        "sonraki_takip": veri.get("sonraki_takip") or None,
        "durum": veri.get("durum") or "Açık",
    }
    if gorusme_id:
        db.guncelle("gorusmeler", gorusme_id, kayit)
        return gorusme_id
    return db.ekle("gorusmeler", kayit)


def gorusme_sil(gorusme_id):
    db.sil("gorusmeler", gorusme_id)


def yaklasan_takipler(gun=7):
    return db.sorgu(
        "SELECT g.*, m.unvan, m.telefon FROM gorusmeler g "
        "JOIN musteriler m ON m.id = g.musteri_id "
        "WHERE g.sonraki_takip IS NOT NULL AND g.sonraki_takip <> '' "
        "AND g.durum = 'Açık' AND g.sonraki_takip <= ? "
        "ORDER BY g.sonraki_takip",
        (gun_ekle(bugun(), gun),),
    )


# --- satislar -------------------------------------------------------------

ODEME_TURLERI = ["Nakit", "Kredi Kartı", "Havale/EFT", "Veresiye"]


def fis_no_uret():
    ay = datetime.now().strftime("%Y%m")
    sayac = db.deger("SELECT COUNT(*) FROM satislar WHERE fis_no LIKE ?", ("SF{}%".format(ay),))
    while True:
        aday = "SF{}-{:03d}".format(ay, sayac + 1)
        if db.tek("SELECT 1 FROM satislar WHERE fis_no = ?", (aday,)) is None:
            return aday
        sayac += 1


def satislar(baslangic=None, bitis=None, arama="", odeme=None):
    kosul, p = [], []
    if baslangic:
        kosul.append("tarih >= ?")
        p.append(baslangic)
    if bitis:
        kosul.append("tarih <= ?")
        p.append(bitis)
    if odeme and odeme != "Tümü":
        kosul.append("odeme_turu = ?")
        p.append(odeme)
    sql = "SELECT * FROM satislar"
    if kosul:
        sql += " WHERE " + " AND ".join(kosul)
    sql += " ORDER BY tarih DESC, id DESC"
    satirlar = db.sorgu(sql, tuple(p))
    if arama:
        satirlar = [s for s in satirlar if icerir(s["fis_no"] + " " + s["musteri_unvan"], arama)]
    return satirlar


def satis(satis_id):
    return db.tek("SELECT * FROM satislar WHERE id = ?", (satis_id,))


def satis_kalemleri(satis_id):
    return db.sorgu("SELECT * FROM satis_kalemleri WHERE satis_id = ? ORDER BY id", (satis_id,))


def satis_kaydet(baslik, kalemler):
    """kalemler: [{urun_id, miktar, birim_fiyat, iskonto}] . Stok dususu burada yapilir."""
    if not kalemler:
        raise IsKurali("Fişe en az bir ürün eklemelisiniz.")

    # Ayni urun birden fazla satirda olabilir. Stogu satir satir degil, urun
    # bazinda topladiktan sonra kontrol ediyorum, yoksa iki satirin toplami
    # stogu asiyor ama tek tek bakinca ikisi de gecerli goruluyor.
    istenen = {}
    for k in kalemler:
        if k["miktar"] <= 0:
            raise IsKurali("Miktar sıfırdan büyük olmalı.")
        istenen[k["urun_id"]] = istenen.get(k["urun_id"], 0) + k["miktar"]

    for urun_id, toplam_miktar in istenen.items():
        u = db.tek("SELECT ad, stok FROM urunler WHERE id = ?", (urun_id,))
        if u is None:
            raise IsKurali("Fişteki bir ürün silinmiş görünüyor.")
        if toplam_miktar > u["stok"]:
            raise IsKurali("'{}' için yeterli stok yok. Mevcut: {:g}, istenen: {:g}".format(
                u["ad"], u["stok"], toplam_miktar))

    if baslik.get("odeme_turu") == "Veresiye" and not baslik.get("musteri_id"):
        raise IsKurali("Veresiye satış için müşteri seçilmeli.")

    ara_toplam = sum(k["miktar"] * k["birim_fiyat"] for k in kalemler)
    satir_iskonto = sum(k["miktar"] * k["birim_fiyat"] * k["iskonto"] / 100.0 for k in kalemler)
    net = ara_toplam - satir_iskonto
    kdv_orani = float(db.ayar("kdv_orani", "20") or 20)
    kdv = net * kdv_orani / 100.0
    toplam = net + kdv

    musteri_id = baslik.get("musteri_id")
    unvan = ""
    if musteri_id:
        m = musteri(musteri_id)
        unvan = m["unvan"] if m else ""
    else:
        unvan = "Perakende Satış"

    # Fis numarasini tek yerde uretiyorum. Once basliga, sonra stok hareketi
    # aciklamasina ayri ayri uretseydim ikisi tutmayabilirdi.
    fis_no = baslik.get("fis_no") or fis_no_uret()

    # Buradan asagisi ya tamamen yazilir ya da hic yazilmaz. Ortada stok kurali
    # patlarsa geride basligi yazilmis, kalemleri eksik bir fis kalmasin.
    with db.islem():
        satis_id = db.ekle("satislar", {
            "fis_no": fis_no,
            "musteri_id": musteri_id,
            "musteri_unvan": unvan,
            "tarih": baslik.get("tarih") or bugun(),
            "ara_toplam": ara_toplam,
            "iskonto": satir_iskonto,
            "kdv": kdv,
            "toplam": toplam,
            "odeme_turu": baslik.get("odeme_turu") or "Nakit",
            "notlar": (baslik.get("notlar") or "").strip(),
            "kullanici_id": baslik.get("kullanici_id"),
        })

        for k in kalemler:
            u = db.tek("SELECT kod, ad FROM urunler WHERE id = ?", (k["urun_id"],))
            tutar = k["miktar"] * k["birim_fiyat"] * (1 - k["iskonto"] / 100.0)
            db.ekle("satis_kalemleri", {
                "satis_id": satis_id,
                "urun_id": k["urun_id"],
                "urun_kod": u["kod"],
                "urun_ad": u["ad"],
                "miktar": k["miktar"],
                "birim_fiyat": k["birim_fiyat"],
                "iskonto": k["iskonto"],
                "tutar": tutar,
            })
            stok_hareketi(k["urun_id"], "Satış", -k["miktar"], "{} nolu fiş".format(fis_no))

        if baslik.get("odeme_turu") == "Veresiye":
            bakiye_ekle(musteri_id, toplam)

    return satis_id


def satis_iptal(satis_id):
    """Fisi siler, stogu geri yukler, veresiye ise bakiyeyi duseler."""
    fis = satis(satis_id)
    if fis is None:
        raise IsKurali("Fiş bulunamadı.")
    # Stok iadesi, bakiye duzeltmesi ve fisin silinmesi tek parca olmali.
    with db.islem():
        for k in satis_kalemleri(satis_id):
            if k["urun_id"]:
                stok_hareketi(k["urun_id"], "İade", k["miktar"],
                              "{} nolu fiş iptali".format(fis["fis_no"]))
        if fis["odeme_turu"] == "Veresiye":
            bakiye_ekle(fis["musteri_id"], -fis["toplam"])
        db.sil("satislar", satis_id)


# --- raporlar / panel -----------------------------------------------------

def panel_ozeti():
    ay = bugun()[:7]
    return {
        "urun_adedi": db.deger("SELECT COUNT(*) FROM urunler WHERE aktif = 1"),
        "kritik_adet": db.deger("SELECT COUNT(*) FROM urunler WHERE aktif = 1 AND stok <= kritik_seviye"),
        "musteri_adedi": db.deger("SELECT COUNT(*) FROM musteriler WHERE aktif = 1"),
        "ay_ciro": float(db.deger("SELECT SUM(toplam) FROM satislar WHERE tarih LIKE ?",
                                  (ay + "%",), varsayilan=0) or 0),
        "ay_fis": db.deger("SELECT COUNT(*) FROM satislar WHERE tarih LIKE ?", (ay + "%",)),
        "toplam_ciro": float(db.deger("SELECT SUM(toplam) FROM satislar", varsayilan=0) or 0),
        "alacak": float(db.deger("SELECT SUM(bakiye) FROM musteriler WHERE bakiye > 0", varsayilan=0) or 0),
    }


def aylik_ciro(adet=6):
    veri = []
    for ay in son_aylar(adet):
        toplam = db.deger("SELECT SUM(toplam) FROM satislar WHERE tarih LIKE ?",
                          (ay[:7] + "%",), varsayilan=0)
        veri.append((ay_etiketi(ay), float(toplam or 0)))
    return veri


def son_satislar(limit=8):
    return db.sorgu("SELECT * FROM satislar ORDER BY tarih DESC, id DESC LIMIT ?", (limit,))


def rapor_satis_ozeti(bas, bit):
    satirlar = db.sorgu(
        "SELECT tarih, COUNT(*) AS fis, SUM(ara_toplam) AS ara, SUM(iskonto) AS isk, "
        "SUM(kdv) AS kdv, SUM(toplam) AS toplam FROM satislar "
        "WHERE tarih BETWEEN ? AND ? GROUP BY tarih ORDER BY tarih DESC",
        (bas, bit),
    )
    return satirlar


def rapor_cok_satan(bas, bit, limit=25):
    return db.sorgu(
        "SELECT k.urun_kod, k.urun_ad, SUM(k.miktar) AS miktar, SUM(k.tutar) AS ciro, "
        "COUNT(DISTINCT k.satis_id) AS fis FROM satis_kalemleri k "
        "JOIN satislar s ON s.id = k.satis_id WHERE s.tarih BETWEEN ? AND ? "
        "GROUP BY k.urun_ad, k.urun_kod ORDER BY ciro DESC LIMIT ?",
        (bas, bit, limit),
    )


def rapor_en_iyi_musteri(bas, bit, limit=25):
    return db.sorgu(
        "SELECT musteri_unvan, COUNT(*) AS fis, SUM(toplam) AS ciro, MAX(tarih) AS son "
        "FROM satislar WHERE tarih BETWEEN ? AND ? "
        "GROUP BY musteri_unvan ORDER BY ciro DESC LIMIT ?",
        (bas, bit, limit),
    )


def rapor_kategori(bas, bit):
    return db.sorgu(
        "SELECT COALESCE(kat.ad, 'Kategorisiz') AS kategori, SUM(k.miktar) AS miktar, "
        "SUM(k.tutar) AS ciro FROM satis_kalemleri k "
        "JOIN satislar s ON s.id = k.satis_id "
        "LEFT JOIN urunler u ON u.id = k.urun_id "
        "LEFT JOIN kategoriler kat ON kat.id = u.kategori_id "
        "WHERE s.tarih BETWEEN ? AND ? GROUP BY kategori ORDER BY ciro DESC",
        (bas, bit),
    )


def rapor_stok_durumu():
    return db.sorgu(
        URUN_SORGU + " WHERE u.aktif = 1 ORDER BY (u.stok * u.alis_fiyati) DESC"
    )


def rapor_odeme_dagilimi(bas, bit):
    return db.sorgu(
        "SELECT odeme_turu, COUNT(*) AS fis, SUM(toplam) AS ciro FROM satislar "
        "WHERE tarih BETWEEN ? AND ? GROUP BY odeme_turu ORDER BY ciro DESC",
        (bas, bit),
    )


# --- kullanici ------------------------------------------------------------

def giris_yap(kullanici_adi, parola):
    k = db.tek("SELECT * FROM kullanicilar WHERE kullanici_adi = ?", ((kullanici_adi or "").strip(),))
    if k is None:
        return None
    if not db.parola_dogrula(parola or "", k["tuz"], k["parola_hash"]):
        return None
    db.calistir("UPDATE kullanicilar SET son_giris = ? WHERE id = ?", (simdi(), k["id"]))
    return dict(k)


def parola_degistir(kullanici_id, eski, yeni):
    k = db.tek("SELECT * FROM kullanicilar WHERE id = ?", (kullanici_id,))
    if k is None or not db.parola_dogrula(eski, k["tuz"], k["parola_hash"]):
        raise IsKurali("Mevcut parola hatalı.")
    if len(yeni) < 4:
        raise IsKurali("Yeni parola en az 4 karakter olmalı.")
    tuz = db.tuz_uret()
    db.guncelle("kullanicilar", kullanici_id, {"tuz": tuz, "parola_hash": db.parola_ozeti(yeni, tuz)})
