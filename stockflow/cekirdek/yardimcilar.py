# -*- coding: utf-8 -*-
# StockFlow · biçimleme ve genel yardimci fonksiyonlar
# Anıl Gül · 2025

import csv
import re
from datetime import date, datetime, timedelta

ISO = "%Y-%m-%d"
ISO_SAAT = "%Y-%m-%d %H:%M:%S"
TR = "%d.%m.%Y"

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

# str.lower() Turkce'de I -> i yapiyor, bize lazim olan I -> ı.
# Arama kutularinda "IŞIK" ile "ışık" eslesmezse kullanici hakli olarak sikayet eder.
_KUCUK_HARF = str.maketrans("IİĞÜŞÖÇ", "ıiğüşöç")
_BUYUK_HARF = str.maketrans("ıiğüşöç", "IİĞÜŞÖÇ")


def kucult(metin):
    if metin is None:
        return ""
    return str(metin).translate(_KUCUK_HARF).lower()


def buyut(metin):
    if metin is None:
        return ""
    return str(metin).translate(_BUYUK_HARF).upper()


def icerir(kaynak, aranan):
    return kucult(aranan) in kucult(kaynak)


def para(deger, sembol=True):
    """1234.5 -> '1.234,50 ₺'"""
    try:
        deger = float(deger or 0)
    except (TypeError, ValueError):
        deger = 0.0
    tam, kusur = "{:,.2f}".format(abs(deger)).split(".")
    tam = tam.replace(",", ".")
    isaret = "-" if deger < -0.004 else ""
    sonuc = "{}{},{}".format(isaret, tam, kusur)
    return sonuc + " ₺" if sembol else sonuc


def sayi(deger, basamak=0):
    try:
        deger = float(deger or 0)
    except (TypeError, ValueError):
        deger = 0.0
    if basamak == 0 and abs(deger - round(deger)) < 0.0001:
        return "{:,}".format(int(round(deger))).replace(",", ".")
    tam, kusur = "{:,.{}f}".format(deger, max(basamak, 2)).split(".")
    return tam.replace(",", ".") + "," + kusur


def yuzde(deger):
    return "%" + sayi(deger, 2).rstrip("0").rstrip(",")


def bugun():
    return date.today().strftime(ISO)


def simdi():
    return datetime.now().strftime(ISO_SAAT)


def tr_tarih(iso_metin):
    """'2025-04-17' -> '17.04.2025'. Saatli gelirse saat kismini atar."""
    if not iso_metin:
        return ""
    metin = str(iso_metin)[:10]
    try:
        return datetime.strptime(metin, ISO).strftime(TR)
    except ValueError:
        return metin


def tr_tarih_saat(iso_metin):
    if not iso_metin:
        return ""
    try:
        d = datetime.strptime(str(iso_metin)[:19], ISO_SAAT)
    except ValueError:
        return tr_tarih(iso_metin)
    return d.strftime("%d.%m.%Y %H:%M")


def iso_tarih(tr_metin):
    """'17.04.2025' -> '2025-04-17'. Cozemezse None."""
    if not tr_metin:
        return None
    metin = str(tr_metin).strip().replace("/", ".").replace("-", ".")
    try:
        return datetime.strptime(metin, TR).strftime(ISO)
    except ValueError:
        return None


def uzun_tarih(iso_metin):
    if not iso_metin:
        return ""
    try:
        d = datetime.strptime(str(iso_metin)[:10], ISO)
    except ValueError:
        return str(iso_metin)
    return "{} {} {} · {}".format(d.day, AYLAR[d.month - 1], d.year, GUNLER[d.weekday()])


def ay_etiketi(iso_metin):
    d = datetime.strptime(str(iso_metin)[:10], ISO)
    return AYLAR[d.month - 1][:3] + " " + str(d.year)[2:]


def gun_ekle(iso_metin, gun):
    d = datetime.strptime(str(iso_metin)[:10], ISO) + timedelta(days=gun)
    return d.strftime(ISO)


def ay_basi(kaydir=0):
    d = date.today().replace(day=1)
    for _ in range(abs(kaydir)):
        if kaydir < 0:
            d = (d - timedelta(days=1)).replace(day=1)
        else:
            d = (d + timedelta(days=32)).replace(day=1)
    return d.strftime(ISO)


def son_aylar(adet=6):
    """Bugunden geriye dogru ay basi tarihleri, eskiden yeniye."""
    liste = []
    for i in range(adet - 1, -1, -1):
        liste.append(ay_basi(-i))
    return liste


def eposta_gecerli(metin):
    if not metin:
        return True  # bos birakilabilir
    return re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", metin.strip()) is not None


def telefon_temizle(metin):
    if not metin:
        return ""
    rakam = re.sub(r"\D", "", metin)
    if len(rakam) == 11 and rakam.startswith("0"):
        rakam = rakam[1:]
    if len(rakam) == 12 and rakam.startswith("90"):
        rakam = rakam[2:]
    if len(rakam) != 10:
        return metin.strip()
    return "0{} {} {} {}".format(rakam[:3], rakam[3:6], rakam[6:8], rakam[8:])


def ondalik(metin, varsayilan=0.0):
    """Kullanici '1.234,50' de yazabilir '1234.5' de. Ikisini de kabul et."""
    if metin is None:
        return varsayilan
    if isinstance(metin, (int, float)):
        return float(metin)
    m = str(metin).strip().replace(" ", "").replace("₺", "")
    if not m:
        return varsayilan
    if "," in m:
        m = m.replace(".", "").replace(",", ".")
    try:
        return float(m)
    except ValueError:
        return varsayilan


def kisalt(metin, uzunluk=40):
    metin = str(metin or "")
    return metin if len(metin) <= uzunluk else metin[:uzunluk - 1] + "…"


def bas_harfler(metin):
    parcalar = [p for p in str(metin or "").split() if p]
    if not parcalar:
        return "?"
    if len(parcalar) == 1:
        return buyut(parcalar[0][:2])
    return buyut(parcalar[0][0] + parcalar[-1][0])


def csv_yaz(yol, basliklar, satirlar):
    # Excel Turkce yerelde ; bekliyor, utf-8-sig olmazsa da harfler bozuluyor.
    with open(yol, "w", newline="", encoding="utf-8-sig") as f:
        yazici = csv.writer(f, delimiter=";")
        yazici.writerow(basliklar)
        yazici.writerows(satirlar)
    return yol
