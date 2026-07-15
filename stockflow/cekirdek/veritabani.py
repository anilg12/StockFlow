# -*- coding: utf-8 -*-
# StockFlow · SQLite baglanti katmani ve tablo semasi
# Anıl Gül · 2025

import hashlib
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .yardimcilar import simdi

KOK = Path(__file__).resolve().parents[2]
VERI_KLASORU = KOK / "veri"
DB_YOLU = VERI_KLASORU / "stockflow.db"
YEDEK_KLASORU = VERI_KLASORU / "yedek"

_baglanti = None
_islem_derinligi = 0  # islem() ic ice cagrilirsa en distaki commit etsin

SEMA = """
CREATE TABLE IF NOT EXISTS kullanicilar (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_adi TEXT NOT NULL UNIQUE,
    parola_hash   TEXT NOT NULL,
    tuz           TEXT NOT NULL,
    ad_soyad      TEXT NOT NULL,
    rol           TEXT NOT NULL DEFAULT 'Personel',
    son_giris     TEXT,
    olusturma     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kategoriler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS urunler (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kod           TEXT NOT NULL UNIQUE,
    ad            TEXT NOT NULL,
    kategori_id   INTEGER REFERENCES kategoriler(id) ON DELETE SET NULL,
    birim         TEXT NOT NULL DEFAULT 'Adet',
    alis_fiyati   REAL NOT NULL DEFAULT 0,
    satis_fiyati  REAL NOT NULL DEFAULT 0,
    stok          REAL NOT NULL DEFAULT 0,
    kritik_seviye REAL NOT NULL DEFAULT 0,
    barkod        TEXT,
    aciklama      TEXT,
    aktif         INTEGER NOT NULL DEFAULT 1,
    olusturma     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS musteriler (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    kod       TEXT NOT NULL UNIQUE,
    unvan     TEXT NOT NULL,
    tip       TEXT NOT NULL DEFAULT 'Bireysel',
    yetkili   TEXT,
    telefon   TEXT,
    eposta    TEXT,
    sehir     TEXT,
    adres     TEXT,
    vergi_no  TEXT,
    bakiye    REAL NOT NULL DEFAULT 0,
    notlar    TEXT,
    aktif     INTEGER NOT NULL DEFAULT 1,
    olusturma TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS satislar (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fis_no        TEXT NOT NULL UNIQUE,
    musteri_id    INTEGER REFERENCES musteriler(id) ON DELETE SET NULL,
    musteri_unvan TEXT NOT NULL DEFAULT '',
    tarih         TEXT NOT NULL,
    ara_toplam    REAL NOT NULL DEFAULT 0,
    iskonto       REAL NOT NULL DEFAULT 0,
    kdv           REAL NOT NULL DEFAULT 0,
    toplam        REAL NOT NULL DEFAULT 0,
    odeme_turu    TEXT NOT NULL DEFAULT 'Nakit',
    notlar        TEXT,
    kullanici_id  INTEGER REFERENCES kullanicilar(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS satis_kalemleri (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    satis_id    INTEGER NOT NULL REFERENCES satislar(id) ON DELETE CASCADE,
    urun_id     INTEGER REFERENCES urunler(id) ON DELETE SET NULL,
    urun_kod    TEXT NOT NULL DEFAULT '',
    urun_ad     TEXT NOT NULL,
    miktar      REAL NOT NULL,
    birim_fiyat REAL NOT NULL,
    iskonto     REAL NOT NULL DEFAULT 0,
    tutar       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS stok_hareketleri (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    urun_id   INTEGER NOT NULL REFERENCES urunler(id) ON DELETE CASCADE,
    tip       TEXT NOT NULL,
    miktar    REAL NOT NULL,
    onceki    REAL NOT NULL DEFAULT 0,
    sonraki   REAL NOT NULL DEFAULT 0,
    aciklama  TEXT,
    tarih     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gorusmeler (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    musteri_id    INTEGER NOT NULL REFERENCES musteriler(id) ON DELETE CASCADE,
    tarih         TEXT NOT NULL,
    tip           TEXT NOT NULL,
    konu          TEXT NOT NULL,
    notlar        TEXT,
    sonraki_takip TEXT,
    durum         TEXT NOT NULL DEFAULT 'Açık'
);

CREATE TABLE IF NOT EXISTS ayarlar (
    anahtar TEXT PRIMARY KEY,
    deger   TEXT
);

CREATE INDEX IF NOT EXISTS ix_satis_tarih    ON satislar(tarih);
CREATE INDEX IF NOT EXISTS ix_satis_musteri  ON satislar(musteri_id);
CREATE INDEX IF NOT EXISTS ix_kalem_satis    ON satis_kalemleri(satis_id);
CREATE INDEX IF NOT EXISTS ix_kalem_urun     ON satis_kalemleri(urun_id);
CREATE INDEX IF NOT EXISTS ix_hareket_urun   ON stok_hareketleri(urun_id);
CREATE INDEX IF NOT EXISTS ix_gorusme_mus    ON gorusmeler(musteri_id);
CREATE INDEX IF NOT EXISTS ix_gorusme_takip  ON gorusmeler(sonraki_takip);
CREATE INDEX IF NOT EXISTS ix_urun_kategori  ON urunler(kategori_id);
"""

VARSAYILAN_AYARLAR = {
    "firma_adi": "Kapadokya Ticaret A.Ş.",
    "firma_adres": "Ürgüp / Nevşehir",
    "firma_telefon": "0384 000 00 00",
    "firma_vergi_no": "0000000000",
    "kdv_orani": "20",
    "para_birimi": "TL",
    "kritik_uyari": "1",
}


def baglanti():
    global _baglanti
    if _baglanti is None:
        VERI_KLASORU.mkdir(parents=True, exist_ok=True)
        _baglanti = sqlite3.connect(str(DB_YOLU))
        _baglanti.row_factory = sqlite3.Row
        _baglanti.execute("PRAGMA foreign_keys = ON")
        _baglanti.execute("PRAGMA journal_mode = WAL")
    return _baglanti


def kapat():
    global _baglanti
    if _baglanti is not None:
        _baglanti.commit()
        _baglanti.close()
        _baglanti = None


def sorgu(sql, p=()):
    return baglanti().execute(sql, p).fetchall()


def tek(sql, p=()):
    return baglanti().execute(sql, p).fetchone()


def deger(sql, p=(), varsayilan=0):
    satir = tek(sql, p)
    if satir is None or satir[0] is None:
        return varsayilan
    return satir[0]


@contextmanager
def islem():
    """Birkac yazmayi tek parca yapar. Ortasinda hata cikarsa hicbiri kalmaz.

    Satis kaydi buna muhtac: fis basligi yazilip kalemlerden biri stok kuralina
    takilirsa geride yarim fis kalmamali. Ic ice cagrilirsa yalnizca en distaki
    commit ediyor, o yuzden sayac tutuyorum.
    """
    global _islem_derinligi
    b = baglanti()
    _islem_derinligi += 1
    try:
        yield b
    except BaseException:
        _islem_derinligi -= 1
        if _islem_derinligi == 0:
            b.rollback()
        raise
    else:
        _islem_derinligi -= 1
        if _islem_derinligi == 0:
            b.commit()


def calistir(sql, p=()):
    b = baglanti()
    imlec = b.execute(sql, p)
    if _islem_derinligi == 0:
        b.commit()
    return imlec.lastrowid


def coklu(sql, kayitlar):
    b = baglanti()
    b.executemany(sql, kayitlar)
    if _islem_derinligi == 0:
        b.commit()


def ekle(tablo, veri):
    kolonlar = ", ".join(veri.keys())
    isaret = ", ".join("?" * len(veri))
    return calistir(
        "INSERT INTO {} ({}) VALUES ({})".format(tablo, kolonlar, isaret),
        tuple(veri.values()),
    )


def guncelle(tablo, kayit_id, veri):
    atama = ", ".join("{} = ?".format(k) for k in veri)
    calistir(
        "UPDATE {} SET {} WHERE id = ?".format(tablo, atama),
        tuple(veri.values()) + (kayit_id,),
    )


def sil(tablo, kayit_id):
    calistir("DELETE FROM {} WHERE id = ?".format(tablo), (kayit_id,))


# --- parola ---------------------------------------------------------------

def tuz_uret():
    return os.urandom(16).hex()


def parola_ozeti(parola, tuz):
    # pbkdf2 stdlib'de var, disaridan bcrypt cekmeye gerek yok.
    return hashlib.pbkdf2_hmac("sha256", parola.encode("utf-8"), tuz.encode("utf-8"), 120000).hex()


def parola_dogrula(parola, tuz, ozet):
    return parola_ozeti(parola, tuz) == ozet


# --- ayarlar --------------------------------------------------------------

def ayar(anahtar, varsayilan=""):
    satir = tek("SELECT deger FROM ayarlar WHERE anahtar = ?", (anahtar,))
    return satir["deger"] if satir else varsayilan


def ayar_yaz(anahtar, deger):
    calistir(
        "INSERT INTO ayarlar (anahtar, deger) VALUES (?, ?) "
        "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger",
        (anahtar, str(deger)),
    )


# --- kurulum / bakim ------------------------------------------------------

def kur():
    b = baglanti()
    b.executescript(SEMA)
    b.commit()

    if deger("SELECT COUNT(*) FROM kullanicilar") == 0:
        tuz = tuz_uret()
        ekle("kullanicilar", {
            "kullanici_adi": "admin",
            "parola_hash": parola_ozeti("1234", tuz),
            "tuz": tuz,
            "ad_soyad": "Anıl Gül",
            "rol": "Yönetici",
            "olusturma": simdi(),
        })

    for anahtar, d in VARSAYILAN_AYARLAR.items():
        if tek("SELECT 1 FROM ayarlar WHERE anahtar = ?", (anahtar,)) is None:
            ayar_yaz(anahtar, d)


def yedekle(hedef_klasor=None):
    """Acik baglanti uzerinden guvenli kopya alir."""
    hedef_klasor = Path(hedef_klasor) if hedef_klasor else YEDEK_KLASORU
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    ad = "stockflow_{}.db".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    hedef = hedef_klasor / ad
    kaynak = baglanti()
    kopya = sqlite3.connect(str(hedef))
    with kopya:
        kaynak.backup(kopya)
    kopya.close()
    return hedef


def geri_yukle(kaynak_dosya):
    global _baglanti
    kapat()
    shutil.copyfile(str(kaynak_dosya), str(DB_YOLU))
    baglanti()


def sifirla():
    """Tum tablolari bosaltir, semayi ve varsayilanlari yeniden kurar."""
    global _baglanti
    b = baglanti()
    for tablo in ("satis_kalemleri", "satislar", "stok_hareketleri", "gorusmeler",
                  "urunler", "musteriler", "kategoriler"):
        b.execute("DELETE FROM {}".format(tablo))
    b.execute("DELETE FROM sqlite_sequence")
    b.commit()
    kur()


def boyut_kb():
    try:
        return DB_YOLU.stat().st_size / 1024
    except OSError:
        return 0
