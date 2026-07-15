# -*- coding: utf-8 -*-
# StockFlow · stok yonetimi sayfasi
# Anıl Gül · 2025

import tkinter as tk
from tkinter import filedialog

from .. import tema
from ..ana_pencere import Sayfa
from ..bilesenler import (Alan, AramaKutusu, Buton, CokSatir, Rozet, Secim,
                          Tablo, TemelDialog, onay_kutusu, uyari_kutusu)
from ...cekirdek import servisler as srv
from ...cekirdek.yardimcilar import (csv_yaz, kisalt, ondalik, para, sayi,
                                     tr_tarih_saat)

BIRIMLER = ["Adet", "Kutu", "Paket", "Kg", "Litre", "Metre", "Makara", "Lisans", "Saat"]


class StokSayfasi(Sayfa):
    BASLIK = "Stok"
    ALT_BASLIK = "Ürün kartları, stok seviyeleri ve giriş/çıkış hareketleri"

    def kur(self):
        self.arama_metni = ""
        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.pack(fill="both", expand=True, padx=24, pady=(18, 24))

        arac = tk.Frame(kabuk, bg=tema.ZEMIN)
        arac.pack(fill="x", pady=(0, 12))

        self.arama = AramaKutusu(arac, self._ara, "Ürün adı, kod veya barkod ara", genislik=30)
        self.arama.pack(side="left")

        self.kategori = Secim(arac, "", ["Tümü"], "Tümü", genislik=18, degisince=lambda v: self.yenile())
        self.kategori.pack(side="left", padx=(10, 0))

        self.kritik_degisken = tk.BooleanVar(value=False)
        kritik_kutu = tk.Checkbutton(arac, text=" Sadece kritik", variable=self.kritik_degisken,
                                     command=self.yenile, bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                                     activebackground=tema.ZEMIN, activeforeground=tema.VURGU_ACIK,
                                     selectcolor=tema.PANEL_ACIK, bd=0, highlightthickness=0,
                                     font=tema.f("govde", 9), cursor="hand2")
        kritik_kutu.pack(side="left", padx=(12, 0))

        Buton(arac, "Yeni Ürün", self.yeni_urun, "birincil", genislik=112, ikon="+").pack(
            side="right")
        Buton(arac, "Düzenle", self.duzenle, "ikincil", genislik=94).pack(side="right", padx=6)
        Buton(arac, "Stok Hareketi", self.hareket_ekle, "ikincil", genislik=124).pack(side="right")
        Buton(arac, "CSV", self.disa_aktar, "sade", genislik=64).pack(side="right", padx=6)
        Buton(arac, "Sil", self.sil, "sade", genislik=58).pack(side="right")

        cerceve = tk.Frame(kabuk, bg=tema.PANEL, highlightbackground=tema.KENAR,
                           highlightthickness=1)
        cerceve.pack(fill="both", expand=True)
        self.tablo = Tablo(cerceve, [
            ("kod", "Kod", 92, "w"),
            ("ad", "Ürün Adı", 300, "w"),
            ("kategori", "Kategori", 150, "w"),
            ("birim", "Birim", 70, "center"),
            ("alis", "Alış", 100, "e"),
            ("satis", "Satış", 100, "e"),
            ("kar", "Kâr %", 70, "e"),
            ("stok", "Stok", 80, "e"),
            ("kritik", "Kritik", 70, "e"),
            ("durum", "Durum", 90, "center"),
        ], yukseklik=16, cift_tik=self.duzenle)
        self.tablo.pack(fill="both", expand=True, padx=1, pady=1)

        alt = tk.Frame(kabuk, bg=tema.ZEMIN)
        alt.pack(fill="x", pady=(10, 0))
        self.durum_etiketi = tk.Label(alt, text="", bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                                      font=tema.f("govde", 9), anchor="w")
        self.durum_etiketi.pack(side="left")
        self.deger_etiketi = tk.Label(alt, text="", bg=tema.ZEMIN, fg=tema.YAZI,
                                      font=tema.f("mono", 9, kalin=True), anchor="e")
        self.deger_etiketi.pack(side="right")

    def _ara(self, metin):
        self.arama_metni = metin
        self.yenile()

    def yenile(self):
        mevcut = self.kategori.al()
        secenekler = ["Tümü"] + srv.kategori_adlari()
        self.kategori.secenekleri_yaz(secenekler)
        if mevcut not in secenekler:
            self.kategori.yaz("Tümü")
            mevcut = "Tümü"

        kayitlar = srv.urunler(self.arama_metni, mevcut, self.kritik_degisken.get())
        satirlar = []
        for u in kayitlar:
            kar = 0.0
            if u["alis_fiyati"] > 0:
                kar = (u["satis_fiyati"] - u["alis_fiyati"]) / u["alis_fiyati"] * 100
            if not u["aktif"]:
                durum = "Pasif"
            elif u["stok"] <= 0:
                durum = "Tükendi"
            elif u["stok"] <= u["kritik_seviye"]:
                durum = "Kritik"
            else:
                durum = "Yeterli"
            satirlar.append((u["id"], (
                u["kod"], u["ad"], u["kategori"], u["birim"],
                para(u["alis_fiyati"], False), para(u["satis_fiyati"], False),
                "%{:.0f}".format(kar), sayi(u["stok"]), sayi(u["kritik_seviye"]), durum,
            )))

        def etiketle(_, degerler):
            durum = degerler[9]
            if durum == "Pasif":
                return "pasif"
            if durum == "Tükendi":
                return "kritik"
            if durum == "Kritik":
                return "uyari"
            return None

        self.tablo.doldur(satirlar, etiketle)
        alis, satis = srv.stok_degeri()
        self.durum_etiketi.configure(
            text="{} ürün listeleniyor · {} kritik seviyede".format(
                len(kayitlar), sum(1 for u in kayitlar if u["stok"] <= u["kritik_seviye"])))
        self.deger_etiketi.configure(
            text="Stok maliyeti {}   ·   Satış değeri {}".format(para(alis), para(satis)))

    # --- islemler ---------------------------------------------------------

    def _secili_urun(self, mesaj="Önce listeden bir ürün seçin."):
        kimlik = self.tablo.secili_kimlik()
        if not kimlik:
            uyari_kutusu(self, "Seçim yok", mesaj)
            return None
        return srv.urun(int(kimlik))

    def yeni_urun(self):
        pencere = UrunDialog(self, None)
        self.wait_window(pencere)
        if pencere.sonuc:
            self.yenile()
            self.kabuk.sayfayi_tazele("panel")
            self.kabuk.rozetleri_yenile()
            self.bildir("Ürün eklendi.")

    def duzenle(self):
        u = self._secili_urun("Düzenlemek için bir ürün seçin.")
        if not u:
            return
        pencere = UrunDialog(self, u)
        self.wait_window(pencere)
        if pencere.sonuc:
            self.yenile()
            self.kabuk.sayfayi_tazele("panel")
            self.kabuk.rozetleri_yenile()
            self.bildir("Ürün güncellendi.")

    def sil(self):
        u = self._secili_urun("Silmek için bir ürün seçin.")
        if not u:
            return
        mesaj = "'{}' ürününü silmek istediğinize emin misiniz?".format(u["ad"])
        gecmis = srv.urun_hareketleri(u["id"], 1)
        if gecmis:
            mesaj += "\n\nÜrünün stok hareketleri de silinecek. " \
                     "Geçmiş satış fişlerinde ürün adı kayıtlı kalır."
        if not onay_kutusu(self, "Ürünü sil", mesaj):
            return
        srv.urun_sil(u["id"])
        self.yenile()
        self.kabuk.sayfayi_tazele("panel")
        self.kabuk.rozetleri_yenile()
        self.bildir("Ürün silindi.", "uyari")

    def hareket_ekle(self):
        u = self._secili_urun("Stok hareketi için bir ürün seçin.")
        if not u:
            return
        pencere = HareketDialog(self, u)
        self.wait_window(pencere)
        if pencere.sonuc:
            self.yenile()
            self.kabuk.sayfayi_tazele("panel")
            self.kabuk.rozetleri_yenile()
            self.bildir("Stok hareketi işlendi.")

    def disa_aktar(self):
        satirlar = self.tablo.gorunen_veri()
        if not satirlar:
            uyari_kutusu(self, "Boş liste", "Dışa aktarılacak kayıt yok.")
            return
        yol = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", initialfile="stok_listesi.csv",
            filetypes=[("CSV dosyası", "*.csv")])
        if not yol:
            return
        basliklar = [k[1] for k in self.tablo.kolonlar]
        csv_yaz(yol, basliklar, satirlar)
        self.bildir("{} satır dışa aktarıldı.".format(len(satirlar)))


class UrunDialog(TemelDialog):
    def __init__(self, ust, urun):
        self.urun = urun
        baslik = "Ürün Kartı" if urun else "Yeni Ürün"
        alt = urun["kod"] if urun else ""
        super().__init__(ust, baslik, genislik=620, yukseklik=530, alt_yazi=alt)

    def govde(self, ust):
        u = self.urun
        izgara = tk.Frame(ust, bg=tema.ZEMIN)
        izgara.pack(fill="x")
        izgara.columnconfigure(0, weight=1, uniform="a")
        izgara.columnconfigure(1, weight=1, uniform="a")

        self.kod = Alan(izgara, "ÜRÜN KODU", u["kod"] if u else srv.urun_kodu_uret(), arka=tema.ZEMIN)
        self.kod.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.barkod = Alan(izgara, "BARKOD", u["barkod"] if u else "", arka=tema.ZEMIN)
        self.barkod.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.ad = Alan(ust, "ÜRÜN ADI", u["ad"] if u else "", arka=tema.ZEMIN)
        self.ad.pack(fill="x", pady=(12, 0))

        izgara2 = tk.Frame(ust, bg=tema.ZEMIN)
        izgara2.pack(fill="x", pady=(12, 0))
        izgara2.columnconfigure(0, weight=2, uniform="b")
        izgara2.columnconfigure(1, weight=1, uniform="b")

        self.kategori = Secim(izgara2, "KATEGORİ", srv.kategori_adlari() or ["Genel"],
                              u["kategori"] if u else "", arka=tema.ZEMIN, duzenlenebilir=True)
        self.kategori.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.birim = Secim(izgara2, "BİRİM", BIRIMLER, u["birim"] if u else "Adet", arka=tema.ZEMIN)
        self.birim.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        izgara3 = tk.Frame(ust, bg=tema.ZEMIN)
        izgara3.pack(fill="x", pady=(12, 0))
        for i in range(4):
            izgara3.columnconfigure(i, weight=1, uniform="c")

        self.alis = Alan(izgara3, "ALIŞ FİYATI (₺)", para(u["alis_fiyati"], False) if u else "0,00",
                         arka=tema.ZEMIN)
        self.alis.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.satis = Alan(izgara3, "SATIŞ FİYATI (₺)", para(u["satis_fiyati"], False) if u else "0,00",
                          arka=tema.ZEMIN)
        self.satis.grid(row=0, column=1, sticky="ew", padx=6)
        self.stok = Alan(izgara3, "STOK", sayi(u["stok"]) if u else "0", arka=tema.ZEMIN)
        self.stok.grid(row=0, column=2, sticky="ew", padx=6)
        self.kritik = Alan(izgara3, "KRİTİK SEVİYE", sayi(u["kritik_seviye"]) if u else "0",
                           arka=tema.ZEMIN)
        self.kritik.grid(row=0, column=3, sticky="ew", padx=(6, 0))

        self.kar_etiketi = tk.Label(ust, text="", bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                                    font=tema.f("mono", 9), anchor="w")
        self.kar_etiketi.pack(fill="x", pady=(8, 0))
        for alan in (self.alis.degisken, self.satis.degisken):
            alan.trace_add("write", lambda *a: self._kar_hesapla())
        self._kar_hesapla()

        self.aciklama = CokSatir(ust, "AÇIKLAMA", u["aciklama"] if u else "", satir=3, arka=tema.ZEMIN)
        self.aciklama.pack(fill="x", pady=(12, 0))

        self.aktif = tk.BooleanVar(value=bool(u["aktif"]) if u else True)
        tk.Checkbutton(ust, text=" Ürün aktif (pasif ürünler satışta listelenmez)",
                       variable=self.aktif, bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                       activebackground=tema.ZEMIN, activeforeground=tema.VURGU_ACIK,
                       selectcolor=tema.PANEL_ACIK, bd=0, highlightthickness=0,
                       font=tema.f("govde", 9), cursor="hand2").pack(anchor="w", pady=(12, 0))

        if u:
            hareket = srv.urun_hareketleri(u["id"], 1)
            if hareket:
                tk.Label(ust, text="Son hareket: {} · {} {:+g}".format(
                    tr_tarih_saat(hareket[0]["tarih"]), hareket[0]["tip"], hareket[0]["miktar"]),
                    bg=tema.ZEMIN, fg=tema.YAZI_PASIF, font=tema.f("mono", 8),
                    anchor="w").pack(fill="x", pady=(10, 0))
        self.after(120, self.ad.odak)

    def _kar_hesapla(self):
        alis = ondalik(self.alis.al())
        satis = ondalik(self.satis.al())
        if alis <= 0:
            self.kar_etiketi.configure(text="Kâr marjı hesaplanamadı (alış fiyatı 0).",
                                       fg=tema.YAZI_PASIF)
            return
        oran = (satis - alis) / alis * 100
        self.kar_etiketi.configure(
            text="Birim kâr {}  ·  marj %{:.1f}".format(para(satis - alis), oran),
            fg=tema.BASARI if oran > 0 else tema.TEHLIKE)

    def kaydet(self):
        srv.urun_kaydet({
            "kod": self.kod.al(),
            "ad": self.ad.al(),
            "kategori": self.kategori.al(),
            "birim": self.birim.al(),
            "alis_fiyati": ondalik(self.alis.al()),
            "satis_fiyati": ondalik(self.satis.al()),
            "stok": ondalik(self.stok.al()),
            "kritik_seviye": ondalik(self.kritik.al()),
            "barkod": self.barkod.al(),
            "aciklama": self.aciklama.al(),
            "aktif": self.aktif.get(),
        }, self.urun["id"] if self.urun else None)
        self.sonuc = True
        return True


class HareketDialog(TemelDialog):
    def __init__(self, ust, urun):
        self.urun = urun
        super().__init__(ust, "Stok Hareketi", genislik=560, yukseklik=520,
                         alt_yazi=urun["kod"])

    def govde(self, ust):
        u = self.urun
        bilgi = tk.Frame(ust, bg=tema.PANEL, highlightbackground=tema.KENAR, highlightthickness=1)
        bilgi.pack(fill="x")
        ic = tk.Frame(bilgi, bg=tema.PANEL)
        ic.pack(fill="x", padx=14, pady=12)
        tk.Label(ic, text=u["ad"], bg=tema.PANEL, fg=tema.YAZI,
                 font=tema.f("baslik", 12, kalin=True), anchor="w").pack(fill="x")
        alt = tk.Frame(ic, bg=tema.PANEL)
        alt.pack(fill="x", pady=(6, 0))
        tk.Label(alt, text="Mevcut stok", bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9)).pack(side="left")
        tk.Label(alt, text="{} {}".format(sayi(u["stok"]), u["birim"]), bg=tema.PANEL,
                 fg=tema.VURGU_ACIK, font=tema.f("mono", 11, kalin=True)).pack(side="left", padx=6)
        Rozet(alt, u["kategori"], "gri").pack(side="right")

        satir = tk.Frame(ust, bg=tema.ZEMIN)
        satir.pack(fill="x", pady=(14, 0))
        satir.columnconfigure(0, weight=1, uniform="h")
        satir.columnconfigure(1, weight=1, uniform="h")
        self.tip = Secim(satir, "HAREKET TİPİ", ["Giriş", "Çıkış", "Düzeltme", "İade", "Fire"],
                         "Giriş", arka=tema.ZEMIN, degisince=lambda v: self._onizle())
        self.tip.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.miktar = Alan(satir, "MİKTAR", "1", arka=tema.ZEMIN)
        self.miktar.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.miktar.degisken.trace_add("write", lambda *a: self._onizle())

        self.aciklama = Alan(ust, "AÇIKLAMA", "", arka=tema.ZEMIN,
                             ipucu="Örn: tedarikçi sevkiyatı, sayım farkı, hasarlı ürün")
        self.aciklama.pack(fill="x", pady=(12, 0))

        self.onizleme = tk.Label(ust, text="", bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                                 font=tema.f("mono", 10, kalin=True), anchor="w")
        self.onizleme.pack(fill="x", pady=(12, 0))
        self._onizle()

        tk.Frame(ust, bg=tema.KENAR, height=1).pack(fill="x", pady=14)
        tk.Label(ust, text="SON HAREKETLER", bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 6))
        gecmis = tk.Frame(ust, bg=tema.PANEL, highlightbackground=tema.KENAR, highlightthickness=1)
        gecmis.pack(fill="both", expand=True)
        tablo = Tablo(gecmis, [
            ("tarih", "Tarih", 130, "w"),
            ("tip", "Tip", 80, "center"),
            ("miktar", "Miktar", 70, "e"),
            ("sonraki", "Kalan", 70, "e"),
            ("aciklama", "Açıklama", 190, "w"),
        ], yukseklik=6)
        tablo.pack(fill="both", expand=True, padx=1, pady=1)
        tablo.doldur([
            (h["id"], (tr_tarih_saat(h["tarih"]), h["tip"], "{:+g}".format(h["miktar"]),
                       sayi(h["sonraki"]), kisalt(h["aciklama"] or "", 26)))
            for h in srv.urun_hareketleri(u["id"], 30)
        ], lambda k, d: "basari" if d[2].startswith("+") else "kritik")
        self.after(120, self.miktar.odak)

    def _onizle(self):
        miktar = ondalik(self.miktar.al())
        tip = self.tip.al()
        mevcut = self.urun["stok"]
        if tip == "Düzeltme":
            yeni = miktar
            fark = miktar - mevcut
        else:
            fark = miktar if tip in ("Giriş", "İade") else -miktar
            yeni = mevcut + fark
        renk = tema.TEHLIKE if yeni < 0 else (tema.BASARI if fark >= 0 else tema.UYARI)
        self.onizleme.configure(
            text="{:g}  →  {:g} {}   ({:+g})".format(mevcut, yeni, self.urun["birim"], fark),
            fg=renk)

    def kaydet(self):
        miktar = ondalik(self.miktar.al())
        if miktar <= 0 and self.tip.al() != "Düzeltme":
            raise srv.IsKurali("Miktar sıfırdan büyük olmalı.")
        tip = self.tip.al()
        if tip == "Düzeltme":
            fark = miktar - self.urun["stok"]
        else:
            fark = miktar if tip in ("Giriş", "İade") else -miktar
        aciklama = self.aciklama.al() or "Elle {} işlemi".format(tip.lower())
        srv.stok_hareketi(self.urun["id"], tip, fark, aciklama)
        self.sonuc = True
        return True
