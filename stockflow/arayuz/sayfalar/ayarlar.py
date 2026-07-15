# -*- coding: utf-8 -*-
# StockFlow · ayarlar ve hakkinda sayfasi
# Anıl Gül · 2025

import platform
import sys
import tkinter as tk
from tkinter import filedialog, ttk

from .. import tema
from ..ana_pencere import Sayfa
from ..bilesenler import (Alan, Buton, CokSatir, Rozet, bilgi_kutusu,
                          onay_kutusu, uyari_kutusu, yuvarlak_dikdortgen)
from ... import (ACIKLAMA, GELISTIRICI, ILK_YIL, IMZA, KURUM, PROJE_TURU,
                 SURUM, UYGULAMA_ADI)
from ...cekirdek import demo
from ...cekirdek import servisler as srv
from ...cekirdek import veritabani as db
from ...cekirdek.yardimcilar import ondalik, para, sayi, tr_tarih_saat


class AyarlarSayfasi(Sayfa):
    BASLIK = "Ayarlar"
    ALT_BASLIK = "Firma bilgileri, güvenlik, veri yönetimi ve proje künyesi"

    def kur(self):
        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.pack(fill="both", expand=True, padx=24, pady=(18, 24))

        defter = ttk.Notebook(kabuk, style="SF.TNotebook")
        defter.pack(fill="both", expand=True)
        defter.add(self._firma_sekmesi(defter), text="Firma")
        defter.add(self._guvenlik_sekmesi(defter), text="Güvenlik")
        defter.add(self._veri_sekmesi(defter), text="Veri")
        defter.add(self._hakkinda_sekmesi(defter), text="Hakkında")

    def _kutu(self, ust):
        cer = tk.Frame(ust, bg=tema.PANEL, highlightbackground=tema.KENAR, highlightthickness=1)
        ic = tk.Frame(cer, bg=tema.PANEL)
        ic.pack(fill="both", expand=True, padx=24, pady=22)
        return cer, ic

    # --- firma ------------------------------------------------------------

    def _firma_sekmesi(self, ust):
        cer, ic = self._kutu(ust)
        tk.Label(ic, text="Fiş çıktılarında ve raporlarda kullanılan bilgiler.",
                 bg=tema.PANEL, fg=tema.YAZI_PASIF, font=tema.f("govde", 9),
                 anchor="w").pack(fill="x", pady=(0, 14))

        izgara = tk.Frame(ic, bg=tema.PANEL)
        izgara.pack(fill="x")
        izgara.columnconfigure(0, weight=1, uniform="a")
        izgara.columnconfigure(1, weight=1, uniform="a")

        self.firma_adi = Alan(izgara, "FİRMA ADI", db.ayar("firma_adi"))
        self.firma_adi.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 12))
        self.firma_tel = Alan(izgara, "TELEFON", db.ayar("firma_telefon"))
        self.firma_tel.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 12))
        self.firma_vergi = Alan(izgara, "VERGİ NUMARASI", db.ayar("firma_vergi_no"))
        self.firma_vergi.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 12))
        self.kdv = Alan(izgara, "VARSAYILAN KDV ORANI (%)", db.ayar("kdv_orani", "20"),
                        ipucu="Yeni satış fişlerinde uygulanır")
        self.kdv.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 12))

        self.firma_adres = CokSatir(ic, "ADRES", db.ayar("firma_adres"), satir=3)
        self.firma_adres.pack(fill="x", pady=(0, 16))

        Buton(ic, "Değişiklikleri Kaydet", self._firma_kaydet, "birincil",
              genislik=176).pack(anchor="w")
        return cer

    def _firma_kaydet(self):
        kdv = ondalik(self.kdv.al(), -1)
        if kdv < 0 or kdv > 100:
            uyari_kutusu(self, "Geçersiz oran", "KDV oranı 0 ile 100 arasında olmalı.")
            return
        db.ayar_yaz("firma_adi", self.firma_adi.al())
        db.ayar_yaz("firma_telefon", self.firma_tel.al())
        db.ayar_yaz("firma_vergi_no", self.firma_vergi.al())
        db.ayar_yaz("firma_adres", self.firma_adres.al())
        db.ayar_yaz("kdv_orani", "{:g}".format(kdv))
        self.bildir("Firma bilgileri kaydedildi.")

    # --- guvenlik ---------------------------------------------------------

    def _guvenlik_sekmesi(self, ust):
        cer, ic = self._kutu(ust)
        k = self.kabuk.kullanici
        tk.Label(ic, text="Oturum: {} ({})".format(k["ad_soyad"], k["kullanici_adi"]),
                 bg=tema.PANEL, fg=tema.YAZI, font=tema.f("baslik", 12, kalin=True),
                 anchor="w").pack(fill="x")
        tk.Label(ic, text="Parolalar veritabanında PBKDF2-SHA256 ile, "
                          "her kullanıcıya özel tuz kullanılarak saklanır.",
                 bg=tema.PANEL, fg=tema.YAZI_PASIF, font=tema.f("govde", 9),
                 anchor="w", justify="left").pack(fill="x", pady=(4, 16))

        dar = tk.Frame(ic, bg=tema.PANEL)
        dar.pack(fill="x")
        self.eski_parola = Alan(dar, "MEVCUT PAROLA", "", genislik=30, gizli=True)
        self.eski_parola.pack(anchor="w", pady=(0, 12))
        self.yeni_parola = Alan(dar, "YENİ PAROLA", "", genislik=30, gizli=True)
        self.yeni_parola.pack(anchor="w", pady=(0, 12))
        self.yeni_parola2 = Alan(dar, "YENİ PAROLA (TEKRAR)", "", genislik=30, gizli=True)
        self.yeni_parola2.pack(anchor="w", pady=(0, 16))
        Buton(dar, "Parolayı Değiştir", self._parola_degistir, "birincil",
              genislik=156).pack(anchor="w")

        tk.Frame(ic, bg=tema.KENAR, height=1).pack(fill="x", pady=18)
        son = k.get("son_giris")
        tk.Label(ic, text="Son giriş: {}".format(tr_tarih_saat(son) if son else "ilk oturum"),
                 bg=tema.PANEL, fg=tema.YAZI_PASIF, font=tema.f("mono", 9),
                 anchor="w").pack(fill="x")
        return cer

    def _parola_degistir(self):
        if self.yeni_parola.al() != self.yeni_parola2.al():
            uyari_kutusu(self, "Parolalar eşleşmiyor", "Yeni parolayı iki alana da aynı girin.")
            return
        try:
            srv.parola_degistir(self.kabuk.kullanici["id"], self.eski_parola.al(),
                                self.yeni_parola.al())
        except srv.IsKurali as h:
            uyari_kutusu(self, "Parola değiştirilemedi", str(h))
            return
        for alan in (self.eski_parola, self.yeni_parola, self.yeni_parola2):
            alan.yaz("")
        self.bildir("Parola güncellendi.")

    # --- veri -------------------------------------------------------------

    def _veri_sekmesi(self, ust):
        cer, ic = self._kutu(ust)
        self.veri_ozeti = tk.Label(ic, text="", bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                                   font=tema.f("mono", 9), anchor="w", justify="left")
        self.veri_ozeti.pack(fill="x", pady=(0, 6))
        tk.Label(ic, text=str(db.DB_YOLU), bg=tema.PANEL, fg=tema.YAZI_PASIF,
                 font=tema.f("mono", 8), anchor="w").pack(fill="x", pady=(0, 16))

        satir = tk.Frame(ic, bg=tema.PANEL)
        satir.pack(fill="x")
        Buton(satir, "Yedek Al", self._yedekle, "birincil", genislik=110).pack(side="left")
        Buton(satir, "Yedekten Dön", self._geri_yukle, "ikincil", genislik=126).pack(
            side="left", padx=8)
        Buton(satir, "Örnek Veriyi Yükle", self._demo, "sade", genislik=150).pack(side="left")

        tk.Frame(ic, bg=tema.KENAR, height=1).pack(fill="x", pady=20)
        tk.Label(ic, text="TEHLİKELİ BÖLGE", bg=tema.PANEL, fg=tema.TEHLIKE,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x")
        tk.Label(ic, text="Tüm ürün, müşteri, satış ve görüşme kayıtları silinir. "
                          "Kullanıcı hesapları ve firma ayarları korunur.",
                 bg=tema.PANEL, fg=tema.YAZI_PASIF, font=tema.f("govde", 9),
                 anchor="w", justify="left").pack(fill="x", pady=(4, 12))
        Buton(ic, "Veritabanını Sıfırla", self._sifirla, "tehlike", genislik=170).pack(anchor="w")
        self._veri_ozetini_yaz()
        return cer

    def _veri_ozetini_yaz(self):
        sayilar = {
            "Ürün": db.deger("SELECT COUNT(*) FROM urunler"),
            "Müşteri": db.deger("SELECT COUNT(*) FROM musteriler"),
            "Satış fişi": db.deger("SELECT COUNT(*) FROM satislar"),
            "Fiş kalemi": db.deger("SELECT COUNT(*) FROM satis_kalemleri"),
            "Stok hareketi": db.deger("SELECT COUNT(*) FROM stok_hareketleri"),
            "Görüşme": db.deger("SELECT COUNT(*) FROM gorusmeler"),
        }
        metin = "   ".join("{}: {}".format(a, sayi(b)) for a, b in sayilar.items())
        self.veri_ozeti.configure(
            text="{}\nVeritabanı boyutu: {:.0f} KB".format(metin, db.boyut_kb()))

    def _yedekle(self):
        klasor = filedialog.askdirectory(parent=self, title="Yedek klasörünü seçin")
        if not klasor:
            return
        hedef = db.yedekle(klasor)
        bilgi_kutusu(self, "Yedek alındı", "Dosya:\n{}".format(hedef))

    def _geri_yukle(self):
        yol = filedialog.askopenfilename(parent=self, title="Yedek dosyasını seçin",
                                         filetypes=[("SQLite veritabanı", "*.db")])
        if not yol:
            return
        if not onay_kutusu(self, "Yedekten dön",
                           "Mevcut veriler seçilen yedekle değiştirilecek.\n\n"
                           "Devam edilsin mi?", "Evet, geri yükle"):
            return
        db.geri_yukle(yol)
        self._veri_ozetini_yaz()
        for sayfa in ("panel", "stok", "musteri", "satis", "rapor"):
            self.kabuk.sayfayi_tazele(sayfa)
        self.kabuk.rozetleri_yenile()
        self.bildir("Yedek geri yüklendi.")

    def _demo(self):
        if not demo.bos_mu():
            uyari_kutusu(self, "Veritabanı dolu",
                         "Örnek veri yalnızca boş veritabanına yüklenebilir. "
                         "Önce sıfırlama yapmalısınız.")
            return
        demo.tohumla()
        self._veri_ozetini_yaz()
        for sayfa in ("panel", "stok", "musteri", "satis", "rapor"):
            self.kabuk.sayfayi_tazele(sayfa)
        self.kabuk.rozetleri_yenile()
        self.bildir("Örnek veri yüklendi.")

    def _sifirla(self):
        if not onay_kutusu(self, "Veritabanını sıfırla",
                           "Bütün kayıtlar kalıcı olarak silinecek.\n\n"
                           "Bu işlem geri alınamaz. Devam edilsin mi?",
                           "Evet, sıfırla"):
            return
        db.sifirla()
        self._veri_ozetini_yaz()
        for sayfa in ("panel", "stok", "musteri", "satis", "rapor"):
            self.kabuk.sayfayi_tazele(sayfa)
        self.kabuk.rozetleri_yenile()
        self.bildir("Veritabanı sıfırlandı.", "uyari")

    # --- hakkinda ---------------------------------------------------------

    def _hakkinda_sekmesi(self, ust):
        cer, ic = self._kutu(ust)
        bas = tk.Frame(ic, bg=tema.PANEL)
        bas.pack(fill="x")

        logo = tk.Canvas(bas, width=86, height=64, bg=tema.PANEL, highlightthickness=0)
        logo.pack(side="left", padx=(0, 16))
        for i, (yuk, renk) in enumerate([(16, tema.VURGU_KOYU), (28, tema.VURGU),
                                         (42, tema.VURGU_ACIK)]):
            x = 12 + i * 22
            yuvarlak_dikdortgen(logo, x, 54 - yuk, x + 15, 54, yaricap=3, fill=renk, outline="")
        logo.create_line(6, 60, 80, 60, fill=tema.KENAR, width=2)

        bilgi = tk.Frame(bas, bg=tema.PANEL)
        bilgi.pack(side="left", fill="x", expand=True)
        tk.Label(bilgi, text=UYGULAMA_ADI, bg=tema.PANEL, fg=tema.YAZI,
                 font=tema.f("baslik", 22, kalin=True), anchor="w").pack(fill="x")
        tk.Label(bilgi, text=ACIKLAMA, bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 10), anchor="w").pack(fill="x", pady=(2, 6))
        rozetler = tk.Frame(bilgi, bg=tema.PANEL)
        rozetler.pack(fill="x")
        Rozet(rozetler, "Sürüm " + SURUM, "vurgu").pack(side="left")
        Rozet(rozetler, "Python " + platform.python_version(), "mavi").pack(side="left", padx=5)
        Rozet(rozetler, "Tkinter · SQLite", "mor").pack(side="left")

        tk.Frame(ic, bg=tema.KENAR, height=1).pack(fill="x", pady=18)

        kunye = [
            ("Proje", "{} · {}".format(KURUM, PROJE_TURU)),
            ("Geliştirici", GELISTIRICI),
            ("İlk geliştirme yılı", ILK_YIL),
            ("Mimari", "Katmanlı yapı: çekirdek (veri + iş kuralları) / arayüz (tkinter)"),
            ("Veritabanı", "SQLite 3 · {} tablo · yabancı anahtar kısıtları açık".format(
                db.deger("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' "
                         "AND name NOT LIKE 'sqlite_%'"))),
            ("Bağımlılık", "Yok · yalnızca Python standart kütüphanesi"),
            ("Çalışma ortamı", "{} {} · {}".format(platform.system(), platform.release(),
                                                   sys.executable)),
        ]
        for etiket, deger in kunye:
            satir = tk.Frame(ic, bg=tema.PANEL)
            satir.pack(fill="x", pady=4)
            tk.Label(satir, text=etiket, bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9), width=20, anchor="w").pack(side="left")
            tk.Label(satir, text=deger, bg=tema.PANEL, fg=tema.YAZI,
                     font=tema.f("govde", 10), anchor="w", justify="left",
                     wraplength=560).pack(side="left", fill="x", expand=True)

        tk.Frame(ic, bg=tema.KENAR, height=1).pack(fill="x", pady=18)
        alt = tk.Frame(ic, bg=tema.PANEL)
        alt.pack(fill="x")
        tk.Label(alt, text=IMZA, bg=tema.PANEL, fg=tema.VURGU,
                 font=tema.f("mono", 10, kalin=True), anchor="w").pack(side="left")
        tk.Label(alt, text="Ctrl+1..6 sayfa geçişi   ·   F5 yenile",
                 bg=tema.PANEL, fg=tema.YAZI_PASIF, font=tema.f("mono", 8),
                 anchor="e").pack(side="right")
        return cer

    def yenile(self):
        if hasattr(self, "veri_ozeti"):
            self._veri_ozetini_yaz()
