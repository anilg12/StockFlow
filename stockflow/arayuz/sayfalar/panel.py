# -*- coding: utf-8 -*-
# StockFlow · panel (ozet ekrani)
# Anıl Gül · 2025

import tkinter as tk

from .. import tema
from ..ana_pencere import Sayfa
from ..bilesenler import (BosDurum, HalkaGrafik, IstatistikKarti, Kart, Rozet,
                          SutunGrafik, Tablo, gosterge)
from ...cekirdek import servisler as srv
from ...cekirdek.yardimcilar import ay_basi, bugun, kisalt, para, sayi, tr_tarih


class PanelSayfasi(Sayfa):
    BASLIK = "Panel"
    ALT_BASLIK = "Günün özeti ve dikkat isteyen kayıtlar"

    def kur(self):
        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.pack(fill="both", expand=True, padx=24, pady=(18, 24))

        # ust sira: 4 istatistik karti
        ust = tk.Frame(kabuk, bg=tema.ZEMIN)
        ust.pack(fill="x")
        for i in range(4):
            ust.columnconfigure(i, weight=1, uniform="kart")

        self.kart_urun = IstatistikKarti(ust, "Aktif Ürün", "0", "", tema.VURGU, "▦")
        self.kart_kritik = IstatistikKarti(ust, "Kritik Stok", "0", "", tema.TEHLIKE, "!")
        self.kart_musteri = IstatistikKarti(ust, "Müşteri", "0", "", tema.BILGI, "◕")
        self.kart_ciro = IstatistikKarti(ust, "Bu Ay Ciro", "0", "", tema.BASARI, "↑")
        for i, k in enumerate((self.kart_urun, self.kart_kritik, self.kart_musteri, self.kart_ciro)):
            k.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0))

        # orta sira: ciro grafigi + kategori halkasi
        orta = tk.Frame(kabuk, bg=tema.ZEMIN)
        orta.pack(fill="both", expand=True, pady=(14, 0))
        orta.columnconfigure(0, weight=3, uniform="orta")
        orta.columnconfigure(1, weight=2, uniform="orta")
        orta.rowconfigure(0, weight=1)

        grafik_kart = Kart(orta, "Son 6 Ayın Cirosu")
        grafik_kart.grid(row=0, column=0, sticky="nsew")
        self.grafik = SutunGrafik(grafik_kart.govde, yukseklik=215)
        self.grafik.pack(fill="both", expand=True)

        self.halka_kart = Kart(orta, "Bu Ay Kategori Dağılımı")
        self.halka_kart.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        halka_ic = tk.Frame(self.halka_kart.govde, bg=tema.PANEL)
        halka_ic.pack(fill="both", expand=True)
        self.halka = HalkaGrafik(halka_ic, boyut=178)
        self.halka.pack(side="left")
        self.gosterge_cer = tk.Frame(halka_ic, bg=tema.PANEL)
        self.gosterge_cer.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # alt sira: son satislar + kritik stok + takipler
        alt = tk.Frame(kabuk, bg=tema.ZEMIN)
        alt.pack(fill="both", expand=True, pady=(14, 0))
        alt.columnconfigure(0, weight=3, uniform="alt")
        alt.columnconfigure(1, weight=2, uniform="alt")
        alt.columnconfigure(2, weight=2, uniform="alt")
        alt.rowconfigure(0, weight=1)

        satis_kart = Kart(alt, "Son Satışlar")
        satis_kart.grid(row=0, column=0, sticky="nsew")
        self.satis_tablo = Tablo(satis_kart.govde, [
            ("fis", "Fiş No", 110, "w"),
            ("musteri", "Müşteri", 170, "w"),
            ("tarih", "Tarih", 82, "center"),
            ("toplam", "Tutar", 100, "e"),
        ], yukseklik=7)
        self.satis_tablo.pack(fill="both", expand=True)

        self.kritik_kart = Kart(alt, "Kritik Stok")
        self.kritik_kart.grid(row=0, column=1, sticky="nsew", padx=14)
        self.kritik_cer = tk.Frame(self.kritik_kart.govde, bg=tema.PANEL)
        self.kritik_cer.pack(fill="both", expand=True)

        self.takip_kart = Kart(alt, "Yaklaşan Takipler")
        self.takip_kart.grid(row=0, column=2, sticky="nsew")
        self.takip_cer = tk.Frame(self.takip_kart.govde, bg=tema.PANEL)
        self.takip_cer.pack(fill="both", expand=True)

    def yenile(self):
        ozet = srv.panel_ozeti()
        alis, satis_degeri = srv.stok_degeri()

        self.kart_urun.guncelle(sayi(ozet["urun_adedi"]),
                                "Stok maliyeti {}".format(para(alis)))
        self.kart_kritik.guncelle(sayi(ozet["kritik_adet"]),
                                  "Sipariş verilmesi gereken kalem" if ozet["kritik_adet"]
                                  else "Tüm ürünler yeterli seviyede")
        self.kart_musteri.guncelle(sayi(ozet["musteri_adedi"]),
                                   "Açık bakiye {}".format(para(ozet["alacak"])))
        self.kart_ciro.guncelle(para(ozet["ay_ciro"]),
                                "{} fiş · toplam {}".format(sayi(ozet["ay_fis"]),
                                                            para(ozet["toplam_ciro"])))

        self.grafik.ciz(srv.aylik_ciro(6))

        kategori = srv.rapor_kategori(ay_basi(0), bugun())
        veri = [(k["kategori"], float(k["ciro"] or 0)) for k in kategori]
        self.halka.ciz(veri, orta_ust=str(len(veri)), orta_alt="kategori")
        for w in self.gosterge_cer.winfo_children():
            w.destroy()
        if veri:
            gosterge(self.gosterge_cer, veri).pack(fill="x")
        else:
            tk.Label(self.gosterge_cer, text="Bu ay henüz satış yok.", bg=tema.PANEL,
                     fg=tema.YAZI_PASIF, font=tema.f("govde", 9)).pack(pady=20)

        self.satis_tablo.doldur([
            (s["id"], (s["fis_no"], kisalt(s["musteri_unvan"], 24),
                       tr_tarih(s["tarih"]), para(s["toplam"])))
            for s in srv.son_satislar(7)
        ])

        self._kritik_doldur()
        self._takip_doldur()

    def _kritik_doldur(self):
        for w in self.kritik_cer.winfo_children():
            w.destroy()
        kayitlar = srv.kritik_urunler()[:6]
        if not kayitlar:
            BosDurum(self.kritik_cer, "Kritik seviyede ürün yok.", "✓").pack(expand=True)
            return
        for u in kayitlar:
            satir = tk.Frame(self.kritik_cer, bg=tema.PANEL)
            satir.pack(fill="x", pady=4)
            tk.Frame(satir, bg=tema.TEHLIKE if u["stok"] <= 0 else tema.UYARI,
                     width=3, height=30).pack(side="left", padx=(0, 9))
            bilgi = tk.Frame(satir, bg=tema.PANEL)
            bilgi.pack(side="left", fill="x", expand=True)
            tk.Label(bilgi, text=kisalt(u["ad"], 28), bg=tema.PANEL, fg=tema.YAZI,
                     font=tema.f("govde", 9), anchor="w").pack(fill="x")
            tk.Label(bilgi, text=u["kategori"], bg=tema.PANEL, fg=tema.YAZI_PASIF,
                     font=tema.f("govde", 8), anchor="w").pack(fill="x")
            tk.Label(satir, text="{:g} / {:g}".format(u["stok"], u["kritik_seviye"]),
                     bg=tema.PANEL, fg=tema.TEHLIKE if u["stok"] <= 0 else tema.UYARI,
                     font=tema.f("mono", 9, kalin=True)).pack(side="right")

    def _takip_doldur(self):
        for w in self.takip_cer.winfo_children():
            w.destroy()
        kayitlar = srv.yaklasan_takipler(7)[:6]
        if not kayitlar:
            BosDurum(self.takip_cer, "Planlanmış görüşme yok.", "✓").pack(expand=True)
            return
        bugunku = bugun()
        for g in kayitlar:
            satir = tk.Frame(self.takip_cer, bg=tema.PANEL)
            satir.pack(fill="x", pady=4)
            gecikti = g["sonraki_takip"] < bugunku
            tk.Frame(satir, bg=tema.TEHLIKE if gecikti else tema.BILGI,
                     width=3, height=30).pack(side="left", padx=(0, 9))
            bilgi = tk.Frame(satir, bg=tema.PANEL)
            bilgi.pack(side="left", fill="x", expand=True)
            tk.Label(bilgi, text=kisalt(g["unvan"], 26), bg=tema.PANEL, fg=tema.YAZI,
                     font=tema.f("govde", 9), anchor="w").pack(fill="x")
            tk.Label(bilgi, text="{} · {}".format(g["tip"], kisalt(g["konu"], 22)),
                     bg=tema.PANEL, fg=tema.YAZI_PASIF,
                     font=tema.f("govde", 8), anchor="w").pack(fill="x")
            Rozet(satir, tr_tarih(g["sonraki_takip"])[:5],
                  "kirmizi" if gecikti else "mavi").pack(side="right")
