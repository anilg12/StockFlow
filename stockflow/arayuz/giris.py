# -*- coding: utf-8 -*-
# StockFlow · oturum acma ekrani
# Anıl Gül · 2025

import tkinter as tk

from . import tema
from .bilesenler import Alan, Buton, yuvarlak_dikdortgen
from .. import ACIKLAMA, IMZA, KURUM, PROJE_TURU, SURUM, UYGULAMA_ADI
from ..cekirdek import servisler as srv


class GirisEkrani(tk.Frame):
    def __init__(self, ust, basarili):
        super().__init__(ust, bg=tema.ZEMIN)
        self.basarili = basarili

        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.place(relx=0.5, rely=0.5, anchor="center")

        self.logo = tk.Canvas(kabuk, width=340, height=104, bg=tema.ZEMIN,
                              highlightthickness=0)
        self.logo.pack()
        self._logo_ciz()

        tk.Label(kabuk, text=UYGULAMA_ADI, bg=tema.ZEMIN, fg=tema.YAZI,
                 font=tema.f("baslik", 27, kalin=True)).pack(pady=(2, 0))
        tk.Label(kabuk, text=ACIKLAMA, bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9)).pack(pady=(2, 20))

        kart = tk.Frame(kabuk, bg=tema.PANEL, highlightbackground=tema.KENAR,
                        highlightthickness=1)
        kart.pack(fill="x")
        tk.Frame(kart, bg=tema.VURGU, height=2).pack(fill="x")
        ic = tk.Frame(kart, bg=tema.PANEL)
        ic.pack(fill="both", padx=26, pady=24)

        self.kullanici = Alan(ic, "KULLANICI ADI", "admin", genislik=26)
        self.kullanici.pack(fill="x")
        self.parola = Alan(ic, "PAROLA", "1234", genislik=26, gizli=True)
        self.parola.pack(fill="x", pady=(14, 0))

        self.hata = tk.Label(ic, text="", bg=tema.PANEL, fg=tema.TEHLIKE,
                             font=tema.f("govde", 9), anchor="w")
        self.hata.pack(fill="x", pady=(10, 0))

        self.dugme = Buton(ic, "Oturum Aç", self.dogrula, "birincil", yukseklik=38)
        self.dugme.pack(fill="x", pady=(4, 0))

        tk.Label(ic, text="Varsayılan hesap · admin / 1234", bg=tema.PANEL,
                 fg=tema.YAZI_PASIF, font=tema.f("mono", 8)).pack(pady=(12, 0))

        alt = tk.Frame(kabuk, bg=tema.ZEMIN)
        alt.pack(fill="x", pady=(20, 0))
        tk.Label(alt, text="{} · {}".format(KURUM, PROJE_TURU), bg=tema.ZEMIN,
                 fg=tema.YAZI_SOLUK, font=tema.f("govde", 9, kalin=True)).pack()
        tk.Label(alt, text="{} · Sürüm {}".format(IMZA, SURUM), bg=tema.ZEMIN,
                 fg=tema.YAZI_PASIF, font=tema.f("mono", 8)).pack(pady=(3, 0))

        for w in (self.kullanici.giris, self.parola.giris):
            w.bind("<Return>", lambda e: self.dogrula())
        self.after(220, self.parola.odak)

    def _logo_ciz(self):
        """Basit bir kutu ve yukselen sutunlar. Disaridan ikon dosyasi tasimamak icin cizerek."""
        t = self.logo
        merkez = 170
        for i, (yuk, renk) in enumerate([(28, tema.VURGU_KOYU), (46, tema.VURGU), (66, tema.VURGU_ACIK)]):
            x = merkez - 44 + i * 34
            yuvarlak_dikdortgen(t, x, 88 - yuk, x + 24, 88, yaricap=5, fill=renk, outline="")
        t.create_line(merkez - 56, 96, merkez + 56, 96, fill=tema.KENAR, width=2)
        t.create_line(merkez + 34, 22, merkez + 52, 22, fill=tema.VURGU_ACIK, width=2)
        t.create_line(merkez + 52, 22, merkez + 52, 40, fill=tema.VURGU_ACIK, width=2)

    def dogrula(self):
        kullanici = srv.giris_yap(self.kullanici.al(), self.parola.al())
        if kullanici is None:
            self.hata.configure(text="Kullanıcı adı veya parola hatalı.")
            self._salla()
            self.parola.yaz("")
            self.parola.odak()
            return
        self.basarili(kullanici)

    def _salla(self, adim=0):
        """Hatali girişte pencereyi hafifce titret. Kucuk detay ama isini goruyor."""
        kok = self.winfo_toplevel()
        if adim == 0:
            self._temel_x = kok.winfo_x()
        if adim >= 8:
            kok.geometry("+{}+{}".format(self._temel_x, kok.winfo_y()))
            return
        kaydir = 7 if adim % 2 == 0 else -7
        kok.geometry("+{}+{}".format(self._temel_x + kaydir, kok.winfo_y()))
        self.after(28, lambda: self._salla(adim + 1))
