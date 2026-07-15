# -*- coding: utf-8 -*-
# StockFlow · ana kabuk: kenar cubugu, ust bar ve sayfa yonlendirme
# Anıl Gül · 2025

import tkinter as tk

from . import tema
from .bilesenler import Avatar, bildirim, yuvarlak_dikdortgen
from .. import IMZA, KURUM, PROJE_TURU, SURUM, UYGULAMA_ADI
from ..cekirdek import servisler as srv
from ..cekirdek.yardimcilar import uzun_tarih, bugun

MENU = [
    ("panel", "Panel", "▤"),
    ("stok", "Stok", "▦"),
    ("musteri", "Müşteriler", "◕"),
    ("satis", "Satışlar", "⇄"),
    ("rapor", "Raporlar", "◭"),
    ("ayarlar", "Ayarlar", "⚙"),
]


class MenuOgesi(tk.Frame):
    def __init__(self, ust, anahtar, metin, ikon, komut):
        super().__init__(ust, bg=tema.PANEL_KOYU, cursor="hand2", height=42)
        self.pack_propagate(False)
        self.anahtar = anahtar
        self.komut = komut
        self.secili = False

        self.serit = tk.Frame(self, bg=tema.PANEL_KOYU, width=3)
        self.serit.pack(side="left", fill="y")
        self.ikon = tk.Label(self, text=ikon, bg=tema.PANEL_KOYU, fg=tema.YAZI_PASIF,
                             font=tema.f("govde", 12), width=3, cursor="hand2")
        self.ikon.pack(side="left", padx=(6, 0))
        self.etiket = tk.Label(self, text=metin, bg=tema.PANEL_KOYU, fg=tema.YAZI_SOLUK,
                               font=tema.f("govde", 10, kalin=True), anchor="w", cursor="hand2")
        self.etiket.pack(side="left", fill="x", expand=True)
        self.rozet = tk.Label(self, text="", bg=tema.TEHLIKE, fg="#FFFFFF",
                              font=tema.f("govde", 8, kalin=True), padx=5)

        for w in (self, self.ikon, self.etiket):
            w.bind("<Enter>", self._gir)
            w.bind("<Leave>", self._cik)
            w.bind("<Button-1>", lambda e: self.komut(self.anahtar))

    def _boya(self, arka, on, serit):
        for w in (self, self.ikon, self.etiket):
            w.configure(bg=arka)
        self.ikon.configure(fg=on)
        self.etiket.configure(fg=on)
        self.serit.configure(bg=serit)

    def _gir(self, _=None):
        if not self.secili:
            self._boya(tema.PANEL, tema.YAZI, tema.PANEL)

    def _cik(self, _=None):
        if not self.secili:
            self._boya(tema.PANEL_KOYU, tema.YAZI_SOLUK, tema.PANEL_KOYU)

    def isaretle(self, secili):
        self.secili = secili
        if secili:
            self._boya(tema.PANEL, tema.VURGU_ACIK, tema.VURGU)
        else:
            self._boya(tema.PANEL_KOYU, tema.YAZI_SOLUK, tema.PANEL_KOYU)

    def rozet_yaz(self, sayi):
        if sayi:
            self.rozet.configure(text=str(sayi))
            self.rozet.pack(side="right", padx=(0, 12))
        else:
            self.rozet.pack_forget()


class AnaPencere(tk.Frame):
    def __init__(self, ust, kullanici, cikis_yap):
        super().__init__(ust, bg=tema.ZEMIN)
        self.kullanici = kullanici
        self.cikis_yap = cikis_yap
        self.sayfalar = {}
        self.aktif = None

        self._kenar_cubugu()
        sag = tk.Frame(self, bg=tema.ZEMIN)
        sag.pack(side="left", fill="both", expand=True)
        self._ust_bar(sag)
        self.icerik = tk.Frame(sag, bg=tema.ZEMIN)
        self.icerik.pack(fill="both", expand=True)

        self.git("panel")
        self.rozetleri_yenile()

        kok = self.winfo_toplevel()
        for i, (anahtar, _, _) in enumerate(MENU, start=1):
            kok.bind("<Control-Key-{}>".format(i), lambda e, a=anahtar: self.git(a))
        kok.bind("<F5>", lambda e: self.yenile())

    # --- kabuk parcalari --------------------------------------------------

    def _kenar_cubugu(self):
        cubuk = tk.Frame(self, bg=tema.PANEL_KOYU, width=214)
        cubuk.pack(side="left", fill="y")
        cubuk.pack_propagate(False)

        logo = tk.Canvas(cubuk, height=76, bg=tema.PANEL_KOYU, highlightthickness=0)
        logo.pack(fill="x")
        for i, (yuk, renk) in enumerate([(12, tema.VURGU_KOYU), (19, tema.VURGU), (27, tema.VURGU_ACIK)]):
            x = 22 + i * 11
            yuvarlak_dikdortgen(logo, x, 48 - yuk, x + 8, 48, yaricap=2, fill=renk, outline="")
        logo.create_text(62, 34, text=UYGULAMA_ADI, anchor="w", fill=tema.YAZI,
                         font=tema.f("baslik", 16, kalin=True))
        logo.create_text(63, 52, text="v" + SURUM, anchor="w", fill=tema.YAZI_PASIF,
                         font=tema.f("mono", 8))

        tk.Frame(cubuk, bg=tema.KENAR, height=1).pack(fill="x", padx=14)

        tk.Label(cubuk, text="MENÜ", bg=tema.PANEL_KOYU, fg=tema.YAZI_PASIF,
                 font=tema.f("govde", 8, kalin=True), anchor="w").pack(
            fill="x", padx=18, pady=(16, 6))

        self.menu_ogeleri = {}
        for anahtar, metin, ikon in MENU:
            oge = MenuOgesi(cubuk, anahtar, metin, ikon, self.git)
            oge.pack(fill="x", pady=1)
            self.menu_ogeleri[anahtar] = oge

        alt = tk.Frame(cubuk, bg=tema.PANEL_KOYU)
        alt.pack(side="bottom", fill="x", pady=(0, 12))
        tk.Label(alt, text="{}\n{}".format(KURUM, PROJE_TURU), bg=tema.PANEL_KOYU,
                 fg=tema.YAZI_PASIF, font=tema.f("govde", 8), justify="left",
                 anchor="w").pack(fill="x", padx=18, pady=(0, 4))
        tk.Label(alt, text=IMZA, bg=tema.PANEL_KOYU, fg=tema.KENAR_ACIK,
                 font=tema.f("mono", 8), anchor="w").pack(fill="x", padx=18)

        kullanici_cer = tk.Frame(cubuk, bg=tema.PANEL)
        kullanici_cer.pack(side="bottom", fill="x", padx=12, pady=12)
        satir = tk.Frame(kullanici_cer, bg=tema.PANEL)
        satir.pack(fill="x", padx=10, pady=10)
        Avatar(satir, self.kullanici["ad_soyad"], boyut=34, renk=tema.VURGU).pack(side="left")
        bilgi = tk.Frame(satir, bg=tema.PANEL)
        bilgi.pack(side="left", fill="x", expand=True, padx=(9, 0))
        tk.Label(bilgi, text=self.kullanici["ad_soyad"], bg=tema.PANEL, fg=tema.YAZI,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x")
        tk.Label(bilgi, text=self.kullanici["rol"], bg=tema.PANEL, fg=tema.YAZI_PASIF,
                 font=tema.f("govde", 8), anchor="w").pack(fill="x")
        cikis = tk.Label(satir, text="⏻", bg=tema.PANEL, fg=tema.YAZI_PASIF,
                         font=tema.f("govde", 12), cursor="hand2")
        cikis.pack(side="right")
        cikis.bind("<Button-1>", lambda e: self.cikis_yap())
        cikis.bind("<Enter>", lambda e: cikis.configure(fg=tema.TEHLIKE))
        cikis.bind("<Leave>", lambda e: cikis.configure(fg=tema.YAZI_PASIF))

    def _ust_bar(self, ust):
        bar = tk.Frame(ust, bg=tema.ZEMIN, height=68)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        sol = tk.Frame(bar, bg=tema.ZEMIN)
        sol.pack(side="left", fill="y", padx=24)
        self.sayfa_basligi = tk.Label(sol, text="", bg=tema.ZEMIN, fg=tema.YAZI,
                                      font=tema.f("baslik", 18, kalin=True), anchor="w")
        self.sayfa_basligi.pack(anchor="w", pady=(15, 0))
        self.sayfa_alt = tk.Label(sol, text="", bg=tema.ZEMIN, fg=tema.YAZI_PASIF,
                                  font=tema.f("govde", 9), anchor="w")
        self.sayfa_alt.pack(anchor="w")

        sag = tk.Frame(bar, bg=tema.ZEMIN)
        sag.pack(side="right", fill="y", padx=24)
        tk.Label(sag, text=uzun_tarih(bugun()), bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9)).pack(side="right", pady=24)
        tk.Frame(ust, bg=tema.KENAR, height=1).pack(fill="x")

    # --- gezinme ----------------------------------------------------------

    def git(self, anahtar):
        if self.aktif == anahtar:
            return
        for a, oge in self.menu_ogeleri.items():
            oge.isaretle(a == anahtar)
        if self.aktif and self.aktif in self.sayfalar:
            self.sayfalar[self.aktif].pack_forget()

        if anahtar not in self.sayfalar:
            self.sayfalar[anahtar] = self._sayfa_uret(anahtar)
        sayfa = self.sayfalar[anahtar]
        sayfa.pack(fill="both", expand=True)
        self.aktif = anahtar

        baslik, alt = sayfa.basliklar()
        self.sayfa_basligi.configure(text=baslik)
        self.sayfa_alt.configure(text=alt)
        sayfa.yenile()
        self.rozetleri_yenile()

    def _sayfa_uret(self, anahtar):
        from .sayfalar import ayarlar, musteri, panel, rapor, stok
        sinif = {
            "panel": panel.PanelSayfasi,
            "stok": stok.StokSayfasi,
            "musteri": musteri.MusteriSayfasi,
            "satis": None,
            "rapor": rapor.RaporSayfasi,
            "ayarlar": ayarlar.AyarlarSayfasi,
        }[anahtar]
        if anahtar == "satis":
            from .sayfalar import satis
            sinif = satis.SatisSayfasi
        return sinif(self.icerik, self)

    def yenile(self):
        if self.aktif and self.aktif in self.sayfalar:
            self.sayfalar[self.aktif].yenile()
        self.rozetleri_yenile()
        bildirim(self, "Veriler yenilendi.", "bilgi", 1500)

    def sayfayi_tazele(self, anahtar):
        """Baska bir sayfada yapilan degisiklik sonrasi onbellekli sayfayi bayatlatir."""
        if anahtar in self.sayfalar and anahtar != self.aktif:
            self.sayfalar[anahtar].destroy()
            del self.sayfalar[anahtar]
        elif anahtar == self.aktif:
            self.sayfalar[anahtar].yenile()

    def rozetleri_yenile(self):
        try:
            self.menu_ogeleri["stok"].rozet_yaz(len(srv.kritik_urunler()))
            self.menu_ogeleri["musteri"].rozet_yaz(len(srv.yaklasan_takipler(0)))
        except Exception:
            pass


class Sayfa(tk.Frame):
    """Tum sayfalarin ortak atasi."""

    BASLIK = ""
    ALT_BASLIK = ""

    def __init__(self, ust, kabuk):
        super().__init__(ust, bg=tema.ZEMIN)
        self.kabuk = kabuk
        self.kur()

    def basliklar(self):
        return self.BASLIK, self.ALT_BASLIK

    def kur(self):
        raise NotImplementedError

    def yenile(self):
        pass

    def bildir(self, metin, tur="basari"):
        bildirim(self, metin, tur)
