# -*- coding: utf-8 -*-
# StockFlow · raporlama sayfasi
# Anıl Gül · 2025

import tkinter as tk
from tkinter import filedialog

from .. import tema
from ..ana_pencere import Sayfa
from ..bilesenler import (Buton, HalkaGrafik, Kart, SutunGrafik, Tablo,
                          TarihGirisi, gosterge, uyari_kutusu)
from ...cekirdek import servisler as srv
from ...cekirdek.yardimcilar import (ay_basi, bugun, csv_yaz, gun_ekle, kisalt,
                                     para, sayi, tr_tarih)

RAPORLAR = [
    "Satış Özeti (günlük)",
    "En Çok Satan Ürünler",
    "En İyi Müşteriler",
    "Kategori Dağılımı",
    "Ödeme Türü Dağılımı",
    "Stok Durumu ve Değeri",
]

HIZLI = [("Bu ay", 0), ("Geçen ay", 1), ("Son 90 gün", 90), ("Bu yıl", 365)]


class RaporSayfasi(Sayfa):
    BASLIK = "Raporlar"
    ALT_BASLIK = "Dönemsel satış, ürün ve stok analizleri"

    def kur(self):
        self.son_veri = ([], [])
        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.pack(fill="both", expand=True, padx=24, pady=(18, 24))

        # --- filtre serit
        filtre = tk.Frame(kabuk, bg=tema.PANEL, highlightbackground=tema.KENAR,
                          highlightthickness=1)
        filtre.pack(fill="x")
        ic = tk.Frame(filtre, bg=tema.PANEL)
        ic.pack(fill="x", padx=16, pady=13)

        sol = tk.Frame(ic, bg=tema.PANEL)
        sol.pack(side="left")
        self.tur = tk.StringVar(value=RAPORLAR[0])
        from tkinter import ttk
        tk.Label(sol, text="RAPOR TÜRÜ", bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 4))
        ttk.Combobox(sol, textvariable=self.tur, values=RAPORLAR, style="SF.TCombobox",
                     state="readonly", width=26, font=tema.f("govde", 10)).pack()

        self.baslangic = TarihGirisi(ic, "BAŞLANGIÇ", ay_basi(0))
        self.baslangic.pack(side="left", padx=(14, 0))
        self.bitis = TarihGirisi(ic, "BİTİŞ", bugun())
        self.bitis.pack(side="left", padx=(10, 0))

        hizli = tk.Frame(ic, bg=tema.PANEL)
        hizli.pack(side="left", padx=(14, 0))
        tk.Label(hizli, text="HIZLI SEÇİM", bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 4))
        dugmeler = tk.Frame(hizli, bg=tema.PANEL)
        dugmeler.pack()
        for metin, _ in HIZLI:
            Buton(dugmeler, metin, lambda m=metin: self._hizli(m), "sade",
                  genislik=78, yukseklik=32).pack(side="left", padx=(0, 4))

        sag = tk.Frame(ic, bg=tema.PANEL)
        sag.pack(side="right")
        tk.Label(sag, text=" ", bg=tema.PANEL, font=tema.f("govde", 9)).pack()
        alt_dugme = tk.Frame(sag, bg=tema.PANEL)
        alt_dugme.pack()
        Buton(alt_dugme, "CSV İndir", self.disa_aktar, "ikincil", genislik=96).pack(side="right")
        Buton(alt_dugme, "Raporla", self.calistir, "birincil", genislik=96).pack(
            side="right", padx=(0, 6))

        # --- ozet kutulari
        self.ozet_serit = tk.Frame(kabuk, bg=tema.ZEMIN)
        self.ozet_serit.pack(fill="x", pady=(14, 0))

        # --- govde
        govde = tk.Frame(kabuk, bg=tema.ZEMIN)
        govde.pack(fill="both", expand=True, pady=(14, 0))
        govde.columnconfigure(0, weight=3, uniform="g")
        govde.columnconfigure(1, weight=2, uniform="g")
        govde.rowconfigure(0, weight=1)

        self.tablo_kart = Kart(govde, "Sonuçlar")
        self.tablo_kart.grid(row=0, column=0, sticky="nsew")
        self.tablo_cer = tk.Frame(self.tablo_kart.govde, bg=tema.PANEL)
        self.tablo_cer.pack(fill="both", expand=True)
        self.tablo = None

        self.grafik_kart = Kart(govde, "Grafik")
        self.grafik_kart.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        self.grafik_cer = tk.Frame(self.grafik_kart.govde, bg=tema.PANEL)
        self.grafik_cer.pack(fill="both", expand=True)

    def _hizli(self, metin):
        if metin == "Bu ay":
            self.baslangic.yaz(ay_basi(0))
            self.bitis.yaz(bugun())
        elif metin == "Geçen ay":
            self.baslangic.yaz(ay_basi(-1))
            self.bitis.yaz(gun_ekle(ay_basi(0), -1))
        elif metin == "Son 90 gün":
            self.baslangic.yaz(gun_ekle(bugun(), -90))
            self.bitis.yaz(bugun())
        else:
            self.baslangic.yaz(bugun()[:4] + "-01-01")
            self.bitis.yaz(bugun())
        self.calistir()

    def yenile(self):
        self.calistir()

    # --- rapor uretimi ----------------------------------------------------

    def calistir(self):
        bas = self.baslangic.al()
        bit = self.bitis.al()
        if not bas or not bit:
            uyari_kutusu(self, "Tarih hatalı", "Tarihleri gg.aa.yyyy biçiminde girin.")
            return
        if bas > bit:
            uyari_kutusu(self, "Tarih hatalı", "Başlangıç tarihi bitiş tarihinden sonra olamaz.")
            return

        tur = self.tur.get()
        uretici = {
            RAPORLAR[0]: self._satis_ozeti,
            RAPORLAR[1]: self._cok_satan,
            RAPORLAR[2]: self._en_iyi_musteri,
            RAPORLAR[3]: self._kategori,
            RAPORLAR[4]: self._odeme,
            RAPORLAR[5]: self._stok,
        }[tur]
        kolonlar, satirlar, grafik, ozetler = uretici(bas, bit)

        self.son_veri = ([k[1] for k in kolonlar], [s[1] for s in satirlar])
        self._tabloyu_kur(kolonlar, satirlar)
        self._ozeti_ciz(ozetler)
        self._grafigi_ciz(grafik, tur)
        self.tablo_kart.basliksatiri.winfo_children()[0].configure(
            text="{} · {} kayıt".format(tur, len(satirlar)))

    def _tabloyu_kur(self, kolonlar, satirlar):
        if self.tablo is not None:
            self.tablo.destroy()
        self.tablo = Tablo(self.tablo_cer, kolonlar, yukseklik=13)
        self.tablo.pack(fill="both", expand=True)
        self.tablo.doldur(satirlar)

    def _ozeti_ciz(self, ozetler):
        for w in self.ozet_serit.winfo_children():
            w.destroy()
        if not ozetler:
            return
        for i in range(len(ozetler)):
            self.ozet_serit.columnconfigure(i, weight=1, uniform="o")
        for i, (etiket, deger, renk) in enumerate(ozetler):
            kutu = tk.Frame(self.ozet_serit, bg=tema.PANEL, highlightbackground=tema.KENAR,
                            highlightthickness=1)
            kutu.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0))
            ic = tk.Frame(kutu, bg=tema.PANEL)
            ic.pack(fill="x", padx=14, pady=11)
            tk.Label(ic, text=etiket.upper(), bg=tema.PANEL, fg=tema.YAZI_PASIF,
                     font=tema.f("govde", 8, kalin=True), anchor="w").pack(fill="x")
            tk.Label(ic, text=deger, bg=tema.PANEL, fg=renk,
                     font=tema.f("mono", 14, kalin=True), anchor="w").pack(fill="x", pady=(4, 0))

    def _grafigi_ciz(self, grafik, tur):
        for w in self.grafik_cer.winfo_children():
            w.destroy()
        if not grafik:
            tk.Label(self.grafik_cer, text="Bu dönem için veri yok.", bg=tema.PANEL,
                     fg=tema.YAZI_PASIF, font=tema.f("govde", 10)).pack(expand=True)
            return
        if tur in (RAPORLAR[3], RAPORLAR[4]):
            halka = HalkaGrafik(self.grafik_cer, boyut=196)
            halka.pack(pady=(4, 10))
            halka.ciz(grafik, orta_ust=str(len(grafik)), orta_alt="kalem")
            gosterge(self.grafik_cer, grafik).pack(fill="x")
        else:
            g = SutunGrafik(self.grafik_cer, yukseklik=240)
            g.pack(fill="both", expand=True)
            g.ciz(grafik[:12])

    # --- rapor tanimlari --------------------------------------------------

    def _satis_ozeti(self, bas, bit):
        kayitlar = srv.rapor_satis_ozeti(bas, bit)
        kolonlar = [("tarih", "Tarih", 110, "w"), ("fis", "Fiş", 70, "e"),
                    ("ara", "Ara Toplam", 120, "e"), ("isk", "İskonto", 110, "e"),
                    ("kdv", "KDV", 110, "e"), ("toplam", "Genel Toplam", 130, "e")]
        satirlar = [(k["tarih"], (tr_tarih(k["tarih"]), sayi(k["fis"]),
                                  para(k["ara"], False), para(k["isk"], False),
                                  para(k["kdv"], False), para(k["toplam"], False)))
                    for k in kayitlar]
        grafik = [(tr_tarih(k["tarih"])[:5], float(k["toplam"] or 0))
                  for k in reversed(kayitlar)][-12:]
        toplam = sum(float(k["toplam"] or 0) for k in kayitlar)
        fis = sum(k["fis"] for k in kayitlar)
        ozet = [("Toplam Ciro", para(toplam), tema.VURGU_ACIK),
                ("Fiş Sayısı", sayi(fis), tema.YAZI),
                ("Ortalama Sepet", para(toplam / fis if fis else 0), tema.YAZI),
                ("Toplam KDV", para(sum(float(k["kdv"] or 0) for k in kayitlar)), tema.YAZI_SOLUK)]
        return kolonlar, satirlar, grafik, ozet

    def _cok_satan(self, bas, bit):
        kayitlar = srv.rapor_cok_satan(bas, bit)
        kolonlar = [("kod", "Kod", 100, "w"), ("ad", "Ürün", 260, "w"),
                    ("miktar", "Miktar", 90, "e"), ("fis", "Fiş", 70, "e"),
                    ("ciro", "Ciro", 130, "e")]
        satirlar = [(k["urun_kod"], (k["urun_kod"], k["urun_ad"], sayi(k["miktar"]),
                                     sayi(k["fis"]), para(k["ciro"], False)))
                    for k in kayitlar]
        grafik = [(kisalt(k["urun_ad"], 9), float(k["ciro"] or 0)) for k in kayitlar[:8]]
        toplam = sum(float(k["ciro"] or 0) for k in kayitlar)
        ozet = [("Ürün Çeşidi", sayi(len(kayitlar)), tema.YAZI),
                ("Satılan Adet", sayi(sum(float(k["miktar"]) for k in kayitlar)), tema.YAZI),
                ("Toplam Ciro", para(toplam), tema.VURGU_ACIK),
                ("En İyi Ürün", kisalt(kayitlar[0]["urun_ad"], 18) if kayitlar else "-",
                 tema.BASARI)]
        return kolonlar, satirlar, grafik, ozet

    def _en_iyi_musteri(self, bas, bit):
        kayitlar = srv.rapor_en_iyi_musteri(bas, bit)
        kolonlar = [("unvan", "Müşteri", 280, "w"), ("fis", "Fiş", 80, "e"),
                    ("ort", "Ort. Sepet", 130, "e"), ("son", "Son Alım", 110, "center"),
                    ("ciro", "Ciro", 130, "e")]
        satirlar = [(k["musteri_unvan"], (
            k["musteri_unvan"], sayi(k["fis"]),
            para(float(k["ciro"] or 0) / k["fis"], False), tr_tarih(k["son"]),
            para(k["ciro"], False))) for k in kayitlar]
        grafik = [(kisalt(k["musteri_unvan"], 9), float(k["ciro"] or 0)) for k in kayitlar[:8]]
        toplam = sum(float(k["ciro"] or 0) for k in kayitlar)
        ozet = [("Müşteri Sayısı", sayi(len(kayitlar)), tema.YAZI),
                ("Toplam Ciro", para(toplam), tema.VURGU_ACIK),
                ("En İyi Müşteri", kisalt(kayitlar[0]["musteri_unvan"], 18) if kayitlar else "-",
                 tema.BASARI),
                ("İlk 3'ün Payı", "%{:.0f}".format(
                    sum(float(k["ciro"] or 0) for k in kayitlar[:3]) / toplam * 100)
                 if toplam else "-", tema.YAZI_SOLUK)]
        return kolonlar, satirlar, grafik, ozet

    def _kategori(self, bas, bit):
        kayitlar = srv.rapor_kategori(bas, bit)
        toplam = sum(float(k["ciro"] or 0) for k in kayitlar)
        kolonlar = [("kategori", "Kategori", 220, "w"), ("miktar", "Miktar", 100, "e"),
                    ("ciro", "Ciro", 140, "e"), ("pay", "Pay", 90, "e")]
        satirlar = [(k["kategori"], (k["kategori"], sayi(k["miktar"]), para(k["ciro"], False),
                                     "%{:.1f}".format(float(k["ciro"] or 0) / toplam * 100
                                                      if toplam else 0)))
                    for k in kayitlar]
        grafik = [(k["kategori"], float(k["ciro"] or 0)) for k in kayitlar]
        ozet = [("Kategori Sayısı", sayi(len(kayitlar)), tema.YAZI),
                ("Toplam Ciro", para(toplam), tema.VURGU_ACIK),
                ("Lider Kategori", kayitlar[0]["kategori"] if kayitlar else "-", tema.BASARI)]
        return kolonlar, satirlar, grafik, ozet

    def _odeme(self, bas, bit):
        kayitlar = srv.rapor_odeme_dagilimi(bas, bit)
        toplam = sum(float(k["ciro"] or 0) for k in kayitlar)
        kolonlar = [("tur", "Ödeme Türü", 200, "w"), ("fis", "Fiş", 90, "e"),
                    ("ciro", "Tutar", 150, "e"), ("pay", "Pay", 90, "e")]
        satirlar = [(k["odeme_turu"], (k["odeme_turu"], sayi(k["fis"]), para(k["ciro"], False),
                                       "%{:.1f}".format(float(k["ciro"] or 0) / toplam * 100
                                                        if toplam else 0)))
                    for k in kayitlar]
        grafik = [(k["odeme_turu"], float(k["ciro"] or 0)) for k in kayitlar]
        veresiye = next((float(k["ciro"] or 0) for k in kayitlar if k["odeme_turu"] == "Veresiye"), 0)
        ozet = [("Toplam Tahsilat", para(toplam - veresiye), tema.BASARI),
                ("Veresiye", para(veresiye), tema.UYARI if veresiye else tema.YAZI_SOLUK),
                ("Fiş Sayısı", sayi(sum(k["fis"] for k in kayitlar)), tema.YAZI)]
        return kolonlar, satirlar, grafik, ozet

    def _stok(self, bas, bit):
        kayitlar = srv.rapor_stok_durumu()
        kolonlar = [("kod", "Kod", 95, "w"), ("ad", "Ürün", 240, "w"),
                    ("kategori", "Kategori", 140, "w"), ("stok", "Stok", 80, "e"),
                    ("maliyet", "Maliyet", 120, "e"), ("deger", "Satış Değeri", 130, "e")]
        satirlar = [(u["kod"], (u["kod"], u["ad"], u["kategori"], sayi(u["stok"]),
                                para(u["stok"] * u["alis_fiyati"], False),
                                para(u["stok"] * u["satis_fiyati"], False)))
                    for u in kayitlar]
        grafik = [(kisalt(u["ad"], 9), u["stok"] * u["alis_fiyati"]) for u in kayitlar[:8]]
        alis, satis = srv.stok_degeri()
        ozet = [("Ürün Çeşidi", sayi(len(kayitlar)), tema.YAZI),
                ("Stok Maliyeti", para(alis), tema.YAZI),
                ("Satış Değeri", para(satis), tema.VURGU_ACIK),
                ("Potansiyel Kâr", para(satis - alis), tema.BASARI)]
        return kolonlar, satirlar, grafik, ozet

    # --- disa aktarim -----------------------------------------------------

    def disa_aktar(self):
        basliklar, satirlar = self.son_veri
        if not satirlar:
            uyari_kutusu(self, "Boş rapor", "Önce raporu çalıştırın.")
            return
        ad = self.tur.get().split("(")[0].strip().replace(" ", "_").lower()
        yol = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", initialfile="{}.csv".format(ad),
            filetypes=[("CSV dosyası", "*.csv")])
        if not yol:
            return
        csv_yaz(yol, basliklar, satirlar)
        self.bildir("{} satır dışa aktarıldı.".format(len(satirlar)))
