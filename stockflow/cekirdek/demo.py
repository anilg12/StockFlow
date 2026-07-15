# -*- coding: utf-8 -*-
# StockFlow · ilk acilista veritabanini doldurmak icin ornek veri
# Bos ekranla karsilasmamak icin. Ayarlar > Veri sekmesinden temizlenebilir.
# Anıl Gül · 2025

import random
from datetime import date, timedelta

from . import servisler as srv
from . import veritabani as db
from .yardimcilar import bugun, simdi

KATEGORILER = [
    "Bilgisayar Donanım",
    "Ağ Ürünleri",
    "Ofis Malzemeleri",
    "Sarf Malzeme",
    "Yazılım Lisans",
    "Çevre Birimleri",
]

URUNLER = [
    # (ad, kategori, birim, alis, satis, stok, kritik)
    ("Kingston Fury 16GB DDR5 5600MHz", "Bilgisayar Donanım", "Adet", 1450, 2090, 34, 10),
    ("Samsung 990 Pro 1TB NVMe SSD", "Bilgisayar Donanım", "Adet", 2780, 3890, 18, 6),
    ("Seagate Barracuda 2TB HDD", "Bilgisayar Donanım", "Adet", 1320, 1850, 7, 8),
    ("Intel Core i5-13400F İşlemci", "Bilgisayar Donanım", "Adet", 5100, 6750, 12, 4),
    ("MSI B760M Gaming Anakart", "Bilgisayar Donanım", "Adet", 3900, 5250, 9, 4),
    ("Corsair RM750e 750W PSU", "Bilgisayar Donanım", "Adet", 2450, 3390, 15, 5),
    ("Arctic Freezer 36 CPU Soğutucu", "Bilgisayar Donanım", "Adet", 690, 1090, 22, 8),
    ("TP-Link Archer AX23 Router", "Ağ Ürünleri", "Adet", 1180, 1690, 26, 8),
    ("Ubiquiti UniFi U6 Lite AP", "Ağ Ürünleri", "Adet", 3250, 4390, 5, 6),
    ("Cat6 UTP Kablo (305m Makara)", "Ağ Ürünleri", "Makara", 2900, 3950, 4, 3),
    ("TP-Link 8 Port Gigabit Switch", "Ağ Ürünleri", "Adet", 620, 940, 31, 10),
    ("Keystone Jack Cat6", "Ağ Ürünleri", "Adet", 28, 55, 240, 50),
    ("Logitech MX Master 3S Mouse", "Çevre Birimleri", "Adet", 2650, 3590, 11, 5),
    ("Logitech K380 Klavye", "Çevre Birimleri", "Adet", 780, 1190, 19, 8),
    ("Dell P2422H 24\" Monitör", "Çevre Birimleri", "Adet", 4200, 5690, 6, 4),
    ("HP LaserJet M110we Yazıcı", "Çevre Birimleri", "Adet", 3100, 4290, 8, 3),
    ("Logitech C920 HD Webcam", "Çevre Birimleri", "Adet", 1750, 2490, 13, 5),
    ("A4 Fotokopi Kağıdı (500 yaprak)", "Ofis Malzemeleri", "Paket", 92, 149, 180, 40),
    ("Faber-Castell Tükenmez Kalem", "Ofis Malzemeleri", "Adet", 9, 19, 420, 100),
    ("Leitz Klasör Geniş", "Ofis Malzemeleri", "Adet", 44, 79, 96, 30),
    ("Post-it Yapışkanlı Not", "Ofis Malzemeleri", "Paket", 38, 69, 140, 40),
    ("HP 305A Toner Siyah", "Sarf Malzeme", "Adet", 1980, 2790, 6, 5),
    ("Canon PG-545 Kartuş", "Sarf Malzeme", "Adet", 640, 949, 14, 6),
    ("Temizlik Spreyi (Ekran)", "Sarf Malzeme", "Adet", 78, 139, 52, 15),
    ("Microsoft 365 Business Standard", "Yazılım Lisans", "Lisans", 4100, 5490, 25, 5),
    ("ESET Endpoint Security 1 Yıl", "Yazılım Lisans", "Lisans", 890, 1390, 40, 10),
    ("Windows 11 Pro OEM", "Yazılım Lisans", "Lisans", 3200, 4390, 17, 6),
]

MUSTERILER = [
    ("Kapadokya Turizm ve Otelcilik Ltd. Şti.", "Kurumsal", "Serhat Aydın", "0384 341 22 18",
     "muhasebe@kapadokyaturizm.com.tr", "Nevşehir", "Ürgüp Merkez, Cumhuriyet Cad. No:14", "4560123789"),
    ("Erciyes Yazılım A.Ş.", "Kurumsal", "Deniz Karabulut", "0352 224 90 41",
     "satinalma@erciyesyazilim.com", "Kayseri", "Melikgazi, Teknopark Blok C/7", "3320987456"),
    ("Anadolu Eğitim Kurumları", "Kurumsal", "Melike Doğan", "0384 213 77 05",
     "bilgi@anadoluegitim.k12.tr", "Nevşehir", "Avanos Yolu 3. Km", "0770456123"),
    ("Gülşehir Market Zinciri", "Kurumsal", "Okan Şahin", "0384 411 65 32",
     "okan.sahin@gulsehirmarket.com", "Nevşehir", "Gülşehir Sanayi Sitesi 4. Blok", "2231456987"),
    ("Mavi Deniz İnşaat", "Kurumsal", "Berk Yalçın", "0322 456 11 09",
     "info@mavidenizinsaat.com", "Adana", "Seyhan, Turhan Cemal Bulvarı No:88", "6540321789"),
    ("Kayseri Ticaret Odası", "Kurumsal", "Nilay Aksoy", "0352 222 45 00",
     "destek@kayserito.org.tr", "Kayseri", "Kocasinan, Ticaret Odası Binası", "5230147852"),
    ("Ahmet Yıldırım", "Bireysel", "", "0532 114 27 63", "ahmet.yildirim@gmail.com", "Nevşehir", "Ürgüp", ""),
    ("Zeynep Korkmaz", "Bireysel", "", "0505 998 41 20", "zeynepkorkmaz@outlook.com", "Kayseri", "Talas", ""),
    ("Mert Özdemir", "Bireysel", "", "0543 762 08 15", "mertozdemir@gmail.com", "Ankara", "Çankaya", ""),
    ("Elif Şengül", "Bireysel", "", "0555 330 76 94", "elif.sengul@yandex.com", "Nevşehir", "Merkez", ""),
    ("Burak Tanrıverdi", "Bireysel", "", "0538 401 55 27", "burakt@hotmail.com", "İstanbul", "Kadıköy", ""),
    ("Selin Arıkan", "Bireysel", "", "0533 267 19 84", "selinarikan@gmail.com", "İzmir", "Bornova", ""),
]

GORUSME_KONULARI = [
    ("Telefon", "Yeni sunucu yenileme talebi", "Mevcut donanımın ömrü dolmuş. Bütçe onayı bekleniyor."),
    ("E-posta", "Fiyat teklifi gönderildi", "12 kalemlik teklif iletildi, geri dönüş bekleniyor."),
    ("Ziyaret", "Yerinde keşif yapıldı", "Kat planı alındı, kablolama için ölçüm tamamlandı."),
    ("Toplantı", "Yıllık sözleşme görüşmesi", "İskonto oranı üzerinde anlaşılamadı, tekrar görüşülecek."),
    ("Şikayet", "Geciken teslimat", "Kargo firması kaynaklı gecikme. Müşteriye bilgi verildi."),
    ("Teklif", "Ağ altyapısı revizyonu", "Access point sayısı 6'dan 9'a çıkarıldı."),
    ("Telefon", "Toner stok sorgusu", "Aylık düzenli sipariş için anlaşma önerildi."),
    ("E-posta", "Fatura düzeltme talebi", "Vergi numarası hatalı girilmiş, düzeltildi."),
    ("Ziyaret", "Kurulum sonrası kontrol", "Sistem sorunsuz çalışıyor. Memnuniyet yüksek."),
    ("Toplantı", "Lisans yenileme planı", "Ocak ayında 25 kullanıcı için yenileme yapılacak."),
    ("Telefon", "Garanti kapsamı sorusu", "2 yıl garanti kapsamında olduğu bilgisi verildi."),
    ("Teklif", "Monitör alımı", "6 adet 24 inç monitör için teklif hazırlandı."),
]


def bos_mu():
    return db.deger("SELECT COUNT(*) FROM urunler") == 0


def tohumla(zorla=False):
    """Veritabani bosken cagrilir. zorla=True ise once temizler."""
    if zorla:
        db.sifirla()
    elif not bos_mu():
        return False

    rastgele = random.Random(2025)  # ayni demo veri her makinede ayni cikssin

    for ad in KATEGORILER:
        srv.kategori_bul_yada_ac(ad)

    urun_idler = []
    for ad, kat, birim, alis, satis, stok, kritik in URUNLER:
        uid = srv.urun_kaydet({
            "kod": srv.urun_kodu_uret(),
            "ad": ad,
            "kategori": kat,
            "birim": birim,
            "alis_fiyati": float(alis),
            "satis_fiyati": float(satis),
            "stok": float(stok),
            "kritik_seviye": float(kritik),
            "barkod": "868{:010d}".format(rastgele.randint(0, 9999999999)),
            "aciklama": "",
            "aktif": True,
        })
        urun_idler.append(uid)

    musteri_idler = []
    for unvan, tip, yetkili, tel, mail, sehir, adres, vergi in MUSTERILER:
        mid = srv.musteri_kaydet({
            "kod": srv.musteri_kodu_uret(),
            "unvan": unvan,
            "tip": tip,
            "yetkili": yetkili,
            "telefon": tel,
            "eposta": mail,
            "sehir": sehir,
            "adres": adres,
            "vergi_no": vergi,
            "aktif": True,
        })
        musteri_idler.append(mid)

    # Son 6 aya yayilmis fisler. Stok yetmeyen kalemi sessizce atliyorum,
    # yoksa demo veri urettikten sonra yari yolda patliyor.
    baslangic = date.today() - timedelta(days=175)
    admin = db.deger("SELECT id FROM kullanicilar ORDER BY id LIMIT 1", varsayilan=1)
    fis_sayisi = 0

    for gun_sayaci in range(176):
        gun = baslangic + timedelta(days=gun_sayaci)

        # Her 20 gunde bir tedarik yapiyoruz. Bunu koymayinca stok ilk aylarda
        # eriyor ve son 2 ay bombos cikiyordu, grafik de sacma gorunuyordu.
        if gun_sayaci % 20 == 0:
            for uid, satir in zip(urun_idler, URUNLER):
                hedef = float(satir[5])
                mevcut = db.deger("SELECT stok FROM urunler WHERE id = ?", (uid,))
                if mevcut < hedef * 0.6:
                    srv.stok_hareketi(uid, "Giriş", hedef - mevcut, "Tedarikçi sevkiyatı")

        if gun.weekday() == 6:
            continue
        for _ in range(rastgele.choice([0, 0, 1, 1, 1, 2, 2, 3])):
            kalemler = []
            secilenler = rastgele.sample(urun_idler, rastgele.randint(1, 4))
            for uid in secilenler:
                u = db.tek("SELECT stok, satis_fiyati FROM urunler WHERE id = ?", (uid,))
                if u["stok"] < 1:
                    continue
                miktar = min(rastgele.randint(1, 5), int(u["stok"]))
                if miktar < 1:
                    continue
                kalemler.append({
                    "urun_id": uid,
                    "miktar": float(miktar),
                    "birim_fiyat": float(u["satis_fiyati"]),
                    "iskonto": rastgele.choice([0, 0, 0, 5, 10]),
                })
            if not kalemler:
                continue
            try:
                srv.satis_kaydet({
                    "musteri_id": rastgele.choice(musteri_idler + [None]),
                    "tarih": gun.strftime("%Y-%m-%d"),
                    "odeme_turu": rastgele.choice(["Nakit", "Kredi Kartı", "Kredi Kartı",
                                                   "Havale/EFT", "Veresiye"]),
                    "kullanici_id": admin,
                    "notlar": "",
                }, kalemler)
                fis_sayisi += 1
            except srv.IsKurali:
                continue

    # Satis sonrasi stok eridi, yeniden dolduralim ki uygulama acilisinda tablo dolu gorunsun.
    for uid, (ad, kat, birim, alis, satis, stok, kritik) in zip(urun_idler, URUNLER):
        mevcut = db.deger("SELECT stok FROM urunler WHERE id = ?", (uid,))
        hedef = float(stok)
        if mevcut < hedef:
            srv.stok_hareketi(uid, "Giriş", hedef - mevcut, "Tedarikçi sevkiyatı")

    for i, konu in enumerate(GORUSME_KONULARI):
        mid = musteri_idler[i % len(musteri_idler)]
        gun = date.today() - timedelta(days=rastgele.randint(0, 60))
        takip = None
        durum = "Kapalı"
        if rastgele.random() < 0.55:
            takip = (date.today() + timedelta(days=rastgele.randint(-3, 12))).strftime("%Y-%m-%d")
            durum = "Açık"
        srv.gorusme_kaydet({
            "musteri_id": mid,
            "tarih": gun.strftime("%Y-%m-%d"),
            "tip": konu[0],
            "konu": konu[1],
            "notlar": konu[2],
            "sonraki_takip": takip,
            "durum": durum,
        })

    return True
