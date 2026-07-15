# -*- coding: utf-8 -*-
# StockFlow · tekrar kullanilan arayuz bilesenleri
# tk.Button yerine Frame+Label kullaniyorum, cunku Windows'ta tk.Button'un
# arka plan rengi ve kenari tam kontrol edilemiyor.
# Anıl Gül · 2025
# Anıl Gül · 2025

import calendar
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from . import tema
from ..cekirdek.yardimcilar import ISO, TR, bas_harfler, iso_tarih, tr_tarih


# --- temel ciziciler ------------------------------------------------------

def yuvarlak_dikdortgen(tuval, x1, y1, x2, y2, yaricap=8, **kw):
    r = min(yaricap, abs(x2 - x1) / 2, abs(y2 - y1) / 2)
    noktalar = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return tuval.create_polygon(noktalar, smooth=True, **kw)


# --- buton ----------------------------------------------------------------

class Buton(tk.Frame):
    STILLER = {
        "birincil": (tema.VURGU, tema.VURGU_ACIK, tema.ZEMIN),
        "ikincil": (tema.PANEL_ACIK, tema.KENAR_ACIK, tema.YAZI),
        "tehlike": (tema.TEHLIKE, "#FF6F6C", "#0C1017"),
        "uyari": (tema.UYARI, "#F5BE5E", "#0C1017"),
        "sade": (tema.PANEL, tema.PANEL_ACIK, tema.YAZI_SOLUK),
        "hayalet": (tema.ZEMIN, tema.PANEL_ACIK, tema.YAZI_SOLUK),
    }

    def __init__(self, ust, metin, komut=None, tur="birincil", genislik=None,
                 yukseklik=34, ikon=None, **kw):
        self._normal, self._hover, self._yazi = self.STILLER.get(tur, self.STILLER["birincil"])
        super().__init__(ust, bg=self._normal, cursor="hand2",
                         highlightthickness=0, bd=0, **kw)
        self.komut = komut
        self._pasif = False
        etiket_metin = "{}  {}".format(ikon, metin) if ikon else metin
        self.etiket = tk.Label(self, text=etiket_metin, bg=self._normal, fg=self._yazi,
                               font=tema.f("govde", 10, kalin=True), cursor="hand2",
                               padx=14, pady=0)
        self.etiket.pack(fill="both", expand=True)
        if genislik:
            self.configure(width=genislik, height=yukseklik)
            self.pack_propagate(False)
            self.grid_propagate(False)
        else:
            self.configure(height=yukseklik)
            self.pack_propagate(False)
            self.grid_propagate(False)
        for w in (self, self.etiket):
            w.bind("<Enter>", self._gir)
            w.bind("<Leave>", self._cik)
            w.bind("<Button-1>", self._bas)
            w.bind("<ButtonRelease-1>", self._birak)

    def _boya(self, renk):
        self.configure(bg=renk)
        self.etiket.configure(bg=renk)

    def _gir(self, _=None):
        if not self._pasif:
            self._boya(self._hover)

    def _cik(self, _=None):
        if not self._pasif:
            self._boya(self._normal)

    def _bas(self, _=None):
        if not self._pasif:
            self._boya(tema.renk_karistir(self._hover, "#000000", 0.25))

    def _birak(self, olay=None):
        if self._pasif:
            return
        self._boya(self._hover)
        if self.komut and olay is not None:
            # Imlec butonun uzerindeyken birakildiysa tiklama sayilir.
            x, y = olay.x, olay.y
            if 0 <= x <= self.winfo_width() and 0 <= y <= self.winfo_height():
                self.komut()

    def metin_ayarla(self, metin):
        self.etiket.configure(text=metin)

    def durum(self, aktif=True):
        self._pasif = not aktif
        if aktif:
            self._boya(self._normal)
            self.etiket.configure(fg=self._yazi, cursor="hand2")
            self.configure(cursor="hand2")
        else:
            self._boya(tema.PANEL)
            self.etiket.configure(fg=tema.YAZI_PASIF, cursor="arrow")
            self.configure(cursor="arrow")


# --- kart ve etiketler ----------------------------------------------------

class Kart(tk.Frame):
    def __init__(self, ust, baslik=None, sag_bilesen=None, dolgu=16, **kw):
        super().__init__(ust, bg=tema.PANEL, highlightbackground=tema.KENAR,
                         highlightcolor=tema.KENAR, highlightthickness=1, bd=0, **kw)
        self.basliksatiri = None
        if baslik:
            self.basliksatiri = tk.Frame(self, bg=tema.PANEL)
            self.basliksatiri.pack(fill="x", padx=dolgu, pady=(dolgu - 2, 0))
            tk.Label(self.basliksatiri, text=baslik, bg=tema.PANEL, fg=tema.YAZI,
                     font=tema.f("baslik", 12, kalin=True)).pack(side="left")
            if sag_bilesen:
                sag_bilesen(self.basliksatiri)
            tk.Frame(self, bg=tema.KENAR, height=1).pack(fill="x", padx=dolgu, pady=(10, 0))
        self.govde = tk.Frame(self, bg=tema.PANEL)
        self.govde.pack(fill="both", expand=True, padx=dolgu, pady=dolgu)


class IstatistikKarti(tk.Frame):
    def __init__(self, ust, baslik, deger, alt="", renk=None, ikon="", **kw):
        super().__init__(ust, bg=tema.PANEL, highlightbackground=tema.KENAR,
                         highlightthickness=1, bd=0, **kw)
        renk = renk or tema.VURGU
        tk.Frame(self, bg=renk, height=3).pack(fill="x", side="top")
        govde = tk.Frame(self, bg=tema.PANEL)
        govde.pack(fill="both", expand=True, padx=16, pady=(12, 14))

        ust_satir = tk.Frame(govde, bg=tema.PANEL)
        ust_satir.pack(fill="x")
        tk.Label(ust_satir, text=baslik.upper(), bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 8, kalin=True)).pack(side="left")
        if ikon:
            tk.Label(ust_satir, text=ikon, bg=tema.PANEL, fg=renk,
                     font=tema.f("govde", 11, kalin=True)).pack(side="right")

        self.deger_etiketi = tk.Label(govde, text=deger, bg=tema.PANEL, fg=tema.YAZI,
                                      font=tema.f("baslik", 21, kalin=True), anchor="w")
        self.deger_etiketi.pack(fill="x", pady=(8, 0))
        self.alt_etiketi = tk.Label(govde, text=alt, bg=tema.PANEL, fg=tema.YAZI_PASIF,
                                    font=tema.f("govde", 9), anchor="w")
        self.alt_etiketi.pack(fill="x", pady=(2, 0))

    def guncelle(self, deger, alt=None):
        self.deger_etiketi.configure(text=deger)
        if alt is not None:
            self.alt_etiketi.configure(text=alt)


class Rozet(tk.Label):
    RENKLER = {
        "yesil": (tema.BASARI, "#132A18"),
        "kirmizi": (tema.TEHLIKE, "#2E1516"),
        "sari": (tema.UYARI, "#2C2312"),
        "mavi": (tema.BILGI, "#141F33"),
        "mor": (tema.MOR, "#211736"),
        "gri": (tema.YAZI_SOLUK, tema.PANEL_ACIK),
        "vurgu": (tema.VURGU_ACIK, tema.VURGU_ISIK),
    }

    def __init__(self, ust, metin, renk="gri", **kw):
        on, arka = self.RENKLER.get(renk, self.RENKLER["gri"])
        super().__init__(ust, text=" {} ".format(metin), bg=arka, fg=on,
                         font=tema.f("govde", 8, kalin=True), padx=6, pady=2, **kw)


def baslik_etiketi(ust, metin, boyut=15, arka=None, renk=None):
    return tk.Label(ust, text=metin, bg=arka or tema.PANEL, fg=renk or tema.YAZI,
                    font=tema.f("baslik", boyut, kalin=True), anchor="w")


def soluk_etiket(ust, metin, boyut=9, arka=None):
    return tk.Label(ust, text=metin, bg=arka or tema.PANEL, fg=tema.YAZI_SOLUK,
                    font=tema.f("govde", boyut), anchor="w")


class Ayirici(tk.Frame):
    def __init__(self, ust, dikey=False, **kw):
        if dikey:
            super().__init__(ust, bg=tema.KENAR, width=1, **kw)
        else:
            super().__init__(ust, bg=tema.KENAR, height=1, **kw)


# --- form alanlari --------------------------------------------------------

class Alan(tk.Frame):
    """Etiketli metin girisi. arka = icinde bulundugu yuzeyin rengi."""

    def __init__(self, ust, etiket, deger="", genislik=24, arka=None, gizli=False,
                 salt_okunur=False, ipucu="", **kw):
        arka = arka or tema.PANEL
        super().__init__(ust, bg=arka, **kw)
        tk.Label(self, text=etiket, bg=arka, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 4))
        self.degisken = tk.StringVar(value=str(deger))
        self.giris = ttk.Entry(self, textvariable=self.degisken, style="SF.TEntry",
                               width=genislik, font=tema.f("govde", 10),
                               show="•" if gizli else "")
        self.giris.pack(fill="x")
        if salt_okunur:
            self.giris.configure(state="readonly")
        if ipucu:
            tk.Label(self, text=ipucu, bg=arka, fg=tema.YAZI_PASIF,
                     font=tema.f("govde", 8), anchor="w").pack(fill="x", pady=(3, 0))

    def al(self):
        return self.degisken.get().strip()

    def yaz(self, deger):
        self.degisken.set("" if deger is None else str(deger))

    def odak(self):
        self.giris.focus_set()


class Secim(tk.Frame):
    def __init__(self, ust, etiket, secenekler, deger="", genislik=22, arka=None,
                 duzenlenebilir=False, degisince=None, **kw):
        arka = arka or tema.PANEL
        super().__init__(ust, bg=arka, **kw)
        tk.Label(self, text=etiket, bg=arka, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 4))
        self.degisken = tk.StringVar(value=deger or (secenekler[0] if secenekler else ""))
        self.kutu = ttk.Combobox(self, textvariable=self.degisken, values=list(secenekler),
                                 style="SF.TCombobox", width=genislik,
                                 font=tema.f("govde", 10),
                                 state="normal" if duzenlenebilir else "readonly")
        self.kutu.pack(fill="x")
        if degisince:
            self.kutu.bind("<<ComboboxSelected>>", lambda e: degisince(self.al()))

    def al(self):
        return self.degisken.get().strip()

    def yaz(self, deger):
        self.degisken.set(deger or "")

    def secenekleri_yaz(self, secenekler):
        self.kutu.configure(values=list(secenekler))


class CokSatir(tk.Frame):
    def __init__(self, ust, etiket, deger="", satir=4, arka=None, **kw):
        arka = arka or tema.PANEL
        super().__init__(ust, bg=arka, **kw)
        tk.Label(self, text=etiket, bg=arka, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 4))
        cerceve = tk.Frame(self, bg=tema.KENAR, padx=1, pady=1)
        cerceve.pack(fill="both", expand=True)
        self.metin = tk.Text(cerceve, height=satir, bg=tema.PANEL_ACIK, fg=tema.YAZI,
                             insertbackground=tema.VURGU, relief="flat", bd=0,
                             font=tema.f("govde", 10), wrap="word", padx=8, pady=6,
                             highlightthickness=0)
        self.metin.pack(fill="both", expand=True)
        if deger:
            self.metin.insert("1.0", deger)
        self.metin.bind("<FocusIn>", lambda e: cerceve.configure(bg=tema.VURGU))
        self.metin.bind("<FocusOut>", lambda e: cerceve.configure(bg=tema.KENAR))

    def al(self):
        return self.metin.get("1.0", "end").strip()

    def yaz(self, deger):
        self.metin.delete("1.0", "end")
        if deger:
            self.metin.insert("1.0", deger)


class AramaKutusu(tk.Frame):
    def __init__(self, ust, komut, ipucu="Ara...", genislik=28, arka=None, **kw):
        arka = arka or tema.ZEMIN
        super().__init__(ust, bg=tema.PANEL_ACIK, highlightbackground=tema.KENAR,
                         highlightthickness=1, bd=0, **kw)
        self.komut = komut
        tk.Label(self, text="⌕", bg=tema.PANEL_ACIK, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 13, kalin=True)).pack(side="left", padx=(9, 2))
        self.degisken = tk.StringVar()
        self.giris = tk.Entry(self, textvariable=self.degisken, bg=tema.PANEL_ACIK,
                              fg=tema.YAZI, relief="flat", bd=0, width=genislik,
                              insertbackground=tema.VURGU, font=tema.f("govde", 10),
                              highlightthickness=0)
        self.giris.pack(side="left", fill="both", expand=True, pady=7)
        self.temizle_dugmesi = tk.Label(self, text="✕", bg=tema.PANEL_ACIK, fg=tema.YAZI_PASIF,
                                        font=tema.f("govde", 9), cursor="hand2", padx=8)
        self.temizle_dugmesi.bind("<Button-1>", lambda e: self.temizle())
        self._ipucu = ipucu
        self._bos_goster()
        self.giris.bind("<FocusIn>", self._odak_gir)
        self.giris.bind("<FocusOut>", self._odak_cik)
        self.degisken.trace_add("write", self._degisti)

    def _bos_goster(self):
        if not self.degisken.get():
            self.giris.configure(fg=tema.YAZI_PASIF)
            self._yer_tutucu = True
            self.giris.insert(0, self._ipucu)

    def _odak_gir(self, _=None):
        self.configure(highlightbackground=tema.VURGU)
        if getattr(self, "_yer_tutucu", False):
            self.giris.delete(0, "end")
            self.giris.configure(fg=tema.YAZI)
            self._yer_tutucu = False

    def _odak_cik(self, _=None):
        self.configure(highlightbackground=tema.KENAR)
        if not self.degisken.get():
            self._bos_goster()

    def _degisti(self, *_):
        if getattr(self, "_yer_tutucu", False):
            return
        if self.degisken.get():
            self.temizle_dugmesi.pack(side="right")
        else:
            self.temizle_dugmesi.pack_forget()
        self.komut(self.degisken.get())

    def al(self):
        return "" if getattr(self, "_yer_tutucu", False) else self.degisken.get()

    def temizle(self):
        self._yer_tutucu = False
        self.degisken.set("")
        self._bos_goster()


# --- takvim ---------------------------------------------------------------

class TakvimSecici(tk.Toplevel):
    """Kucuk acilir takvim. tkcalendar disariya bagimlilik getirdigi icin elde yazdim."""

    def __init__(self, ust, secili, geri_cagir):
        super().__init__(ust)
        self.geri_cagir = geri_cagir
        self.overrideredirect(True)
        self.configure(bg=tema.KENAR)
        self.attributes("-topmost", True)
        try:
            self.secili = datetime.strptime(secili, ISO).date() if secili else date.today()
        except (ValueError, TypeError):
            self.secili = date.today()
        self.gosterilen = self.secili.replace(day=1)

        self.govde = tk.Frame(self, bg=tema.PANEL)
        self.govde.pack(padx=1, pady=1)
        self._basligi_ciz()
        self.izgara = tk.Frame(self.govde, bg=tema.PANEL)
        self.izgara.pack(padx=10, pady=(0, 10))
        self._ayi_ciz()

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<FocusOut>", lambda e: self.after(120, self._odak_kontrol))
        self.after(60, self.focus_force)

    def _odak_kontrol(self):
        try:
            if self.focus_displayof() is None:
                self.destroy()
        except (KeyError, tk.TclError):
            self.destroy()

    def _basligi_ciz(self):
        ust = tk.Frame(self.govde, bg=tema.PANEL)
        ust.pack(fill="x", padx=10, pady=(10, 6))
        for metin, adim in (("‹", -1), ("›", 1)):
            d = tk.Label(ust, text=metin, bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                         font=tema.f("govde", 13, kalin=True), cursor="hand2", padx=6)
            d.pack(side="left" if adim < 0 else "right")
            d.bind("<Button-1>", lambda e, a=adim: self._ay_degistir(a))
            d.bind("<Enter>", lambda e, w=d: w.configure(fg=tema.VURGU_ACIK))
            d.bind("<Leave>", lambda e, w=d: w.configure(fg=tema.YAZI_SOLUK))
        self.baslik = tk.Label(ust, text="", bg=tema.PANEL, fg=tema.YAZI,
                               font=tema.f("baslik", 11, kalin=True))
        self.baslik.pack(side="left", expand=True)

    def _ay_degistir(self, adim):
        ay = self.gosterilen.month + adim
        yil = self.gosterilen.year
        if ay < 1:
            ay, yil = 12, yil - 1
        elif ay > 12:
            ay, yil = 1, yil + 1
        self.gosterilen = date(yil, ay, 1)
        self._ayi_ciz()

    def _ayi_ciz(self):
        from ..cekirdek.yardimcilar import AYLAR, GUNLER
        for w in self.izgara.winfo_children():
            w.destroy()
        self.baslik.configure(text="{} {}".format(AYLAR[self.gosterilen.month - 1],
                                                  self.gosterilen.year))
        for i, g in enumerate(GUNLER):
            tk.Label(self.izgara, text=g, bg=tema.PANEL, fg=tema.YAZI_PASIF,
                     font=tema.f("govde", 8, kalin=True), width=4).grid(row=0, column=i, pady=(0, 4))

        bugun_ = date.today()
        for h, hafta in enumerate(calendar.Calendar(firstweekday=0).monthdatescalendar(
                self.gosterilen.year, self.gosterilen.month), start=1):
            for s, gun in enumerate(hafta):
                bu_ay = gun.month == self.gosterilen.month
                renk = tema.YAZI if bu_ay else tema.YAZI_PASIF
                arka = tema.PANEL
                if gun == self.secili:
                    arka, renk = tema.VURGU, tema.ZEMIN
                elif gun == bugun_:
                    renk = tema.VURGU_ACIK
                h_etiket = tk.Label(self.izgara, text=str(gun.day), bg=arka, fg=renk,
                                    font=tema.f("govde", 9, kalin=(gun == bugun_)),
                                    width=4, pady=3, cursor="hand2")
                h_etiket.grid(row=h, column=s, padx=1, pady=1)
                h_etiket.bind("<Button-1>", lambda e, g=gun: self._sec(g))
                if gun != self.secili:
                    h_etiket.bind("<Enter>", lambda e, w=h_etiket: w.configure(bg=tema.PANEL_ACIK))
                    h_etiket.bind("<Leave>", lambda e, w=h_etiket: w.configure(bg=tema.PANEL))

    def _sec(self, gun):
        self.geri_cagir(gun.strftime(ISO))
        self.destroy()


class TarihGirisi(tk.Frame):
    def __init__(self, ust, etiket, deger=None, arka=None, genislik=14, **kw):
        arka = arka or tema.PANEL
        super().__init__(ust, bg=arka, **kw)
        if etiket:
            tk.Label(self, text=etiket, bg=arka, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9, kalin=True), anchor="w").pack(fill="x", pady=(0, 4))
        kutu = tk.Frame(self, bg=tema.PANEL_ACIK, highlightbackground=tema.KENAR,
                        highlightthickness=1)
        kutu.pack(fill="x")
        self.degisken = tk.StringVar(value=tr_tarih(deger) if deger else "")
        self.giris = tk.Entry(kutu, textvariable=self.degisken, bg=tema.PANEL_ACIK,
                              fg=tema.YAZI, relief="flat", bd=0, width=genislik,
                              insertbackground=tema.VURGU, font=tema.f("mono", 10),
                              highlightthickness=0)
        self.giris.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=7)
        takvim = tk.Label(kutu, text="▤", bg=tema.PANEL_ACIK, fg=tema.YAZI_SOLUK,
                          font=tema.f("govde", 11), cursor="hand2", padx=8)
        takvim.pack(side="right")
        takvim.bind("<Button-1>", lambda e: self._takvim_ac())
        takvim.bind("<Enter>", lambda e: takvim.configure(fg=tema.VURGU_ACIK))
        takvim.bind("<Leave>", lambda e: takvim.configure(fg=tema.YAZI_SOLUK))
        self.giris.bind("<FocusIn>", lambda e: kutu.configure(highlightbackground=tema.VURGU))
        self.giris.bind("<FocusOut>", lambda e: kutu.configure(highlightbackground=tema.KENAR))

    def _takvim_ac(self):
        pencere = TakvimSecici(self.winfo_toplevel(), self.al(), self.yaz)
        pencere.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        ekran_h = self.winfo_screenheight()
        if y + pencere.winfo_height() > ekran_h:
            y = self.winfo_rooty() - pencere.winfo_height() - 4
        pencere.geometry("+{}+{}".format(x, y))

    def al(self):
        return iso_tarih(self.degisken.get())

    def yaz(self, iso_deger):
        self.degisken.set(tr_tarih(iso_deger) if iso_deger else "")


# --- tablo ----------------------------------------------------------------

class Tablo(tk.Frame):
    """ttk.Treeview sarmalayici. kolonlar: [(anahtar, baslik, genislik, hiza)]"""

    def __init__(self, ust, kolonlar, yukseklik=12, cift_tik=None, secilince=None, **kw):
        super().__init__(ust, bg=tema.PANEL, **kw)
        self.kolonlar = kolonlar
        self._siralama = {}
        anahtarlar = [k[0] for k in kolonlar]

        self.agac = ttk.Treeview(self, columns=anahtarlar, show="headings",
                                 height=yukseklik, selectmode="browse")
        kaydirici = ttk.Scrollbar(self, orient="vertical", style="SF.Vertical.TScrollbar",
                                  command=self.agac.yview)
        self.agac.configure(yscrollcommand=kaydirici.set)
        self.agac.pack(side="left", fill="both", expand=True)
        kaydirici.pack(side="right", fill="y")

        for anahtar, baslik, genislik, hiza in kolonlar:
            self.agac.heading(anahtar, text=baslik,
                              command=lambda a=anahtar: self._sirala(a))
            self.agac.column(anahtar, width=genislik, minwidth=40, anchor=hiza,
                             stretch=(hiza == "w"))

        self.agac.tag_configure("tek", background=tema.PANEL)
        self.agac.tag_configure("cift", background=tema.ZEBRA)
        self.agac.tag_configure("kritik", foreground=tema.TEHLIKE)
        self.agac.tag_configure("uyari", foreground=tema.UYARI)
        self.agac.tag_configure("basari", foreground=tema.BASARI)
        self.agac.tag_configure("pasif", foreground=tema.YAZI_PASIF)

        if cift_tik:
            self.agac.bind("<Double-1>", lambda e: cift_tik())
            self.agac.bind("<Return>", lambda e: cift_tik())
        if secilince:
            self.agac.bind("<<TreeviewSelect>>", lambda e: secilince())

    def doldur(self, satirlar, etiketleyici=None):
        """satirlar: [(kimlik, [deger, ...])]"""
        secili = self.secili_kimlik()
        self.agac.delete(*self.agac.get_children())
        for i, (kimlik, degerler) in enumerate(satirlar):
            etiketler = ["cift" if i % 2 else "tek"]
            if etiketleyici:
                ek = etiketleyici(kimlik, degerler)
                if ek:
                    etiketler.append(ek)
            self.agac.insert("", "end", iid=str(kimlik), values=degerler, tags=tuple(etiketler))
        if secili and self.agac.exists(str(secili)):
            self.agac.selection_set(str(secili))
            self.agac.see(str(secili))

    def _sirala(self, anahtar):
        ters = self._siralama.get(anahtar, False)
        veri = [(self.agac.set(k, anahtar), k) for k in self.agac.get_children("")]

        def anahtarla(ikili):
            ham = ikili[0].replace("₺", "").replace(".", "").replace(",", ".").strip()
            try:
                return (0, float(ham))
            except ValueError:
                return (1, ikili[0].lower())

        veri.sort(key=anahtarla, reverse=ters)
        for indeks, (_, k) in enumerate(veri):
            self.agac.move(k, "", indeks)
            mevcut = [t for t in self.agac.item(k, "tags") if t not in ("tek", "cift")]
            self.agac.item(k, tags=tuple(mevcut + ["cift" if indeks % 2 else "tek"]))
        self._siralama[anahtar] = not ters
        for a, b, _, _ in self.kolonlar:
            ok = ("  ▾" if ters else "  ▴") if a == anahtar else ""
            self.agac.heading(a, text=b + ok)

    def secili_kimlik(self):
        secim = self.agac.selection()
        return secim[0] if secim else None

    def secimi_temizle(self):
        self.agac.selection_remove(*self.agac.selection())

    def satir_sayisi(self):
        return len(self.agac.get_children())

    def gorunen_veri(self):
        return [self.agac.item(k, "values") for k in self.agac.get_children()]


class BosDurum(tk.Frame):
    def __init__(self, ust, metin, ikon="◌", arka=None, **kw):
        arka = arka or tema.PANEL
        super().__init__(ust, bg=arka, **kw)
        tk.Label(self, text=ikon, bg=arka, fg=tema.KENAR_ACIK,
                 font=tema.f("govde", 28)).pack(pady=(20, 6))
        tk.Label(self, text=metin, bg=arka, fg=tema.YAZI_PASIF,
                 font=tema.f("govde", 10)).pack(pady=(0, 20))


# --- grafikler ------------------------------------------------------------

class SutunGrafik(tk.Canvas):
    def __init__(self, ust, yukseklik=200, renk=None, **kw):
        super().__init__(ust, bg=tema.PANEL, height=yukseklik, highlightthickness=0, bd=0, **kw)
        self.renk = renk or tema.VURGU
        self.veriler = []
        self._adim = 0
        self._is = None
        self._ipucu = None
        self.bind("<Configure>", lambda e: self._ciz(self._adim))
        self.bind("<Motion>", self._imlec)
        self.bind("<Leave>", lambda e: self._ipucu_gizle())

    def ciz(self, veriler, animasyon=True):
        self.veriler = list(veriler)
        if self._is:
            try:
                self.after_cancel(self._is)
            except (ValueError, tk.TclError):
                pass
            self._is = None
        if animasyon:
            self._adim = 0
            self._canlandir()
        else:
            self._adim = 12
            self._ciz(12)

    def _canlandir(self):
        if not self.winfo_exists():
            return
        self._adim += 1
        self._ciz(self._adim)
        if self._adim < 12:
            self._is = self.after(22, self._canlandir)

    def _ciz(self, adim):
        if not self.winfo_exists():
            return
        self.delete("all")
        g = self.winfo_width()
        y = self.winfo_height()
        if g < 60 or y < 60 or not self.veriler:
            return

        sol, sag, ust, alt = 62, 12, 14, 30
        alan_g = g - sol - sag
        alan_y = y - ust - alt
        enb = max([d for _, d in self.veriler] + [1])
        # Ust siniri yuvarlak bir sayiya cekiyorum, cizgi etiketleri daha temiz cikiyor.
        basamak = 10 ** max(len(str(int(enb))) - 2, 0)
        tavan = ((int(enb / basamak) + 1) * basamak) if basamak else enb * 1.1
        tavan = max(tavan, 1)

        for i in range(5):
            gy = ust + alan_y * i / 4
            self.create_line(sol, gy, g - sag, gy, fill=tema.KENAR if i == 4 else tema.ZEBRA)
            deger = tavan * (4 - i) / 4
            self.create_text(sol - 8, gy, text=self._kisa(deger), anchor="e",
                             fill=tema.YAZI_PASIF, font=tema.f("mono", 8))

        adet = len(self.veriler)
        bosluk = alan_g / adet
        sutun_g = min(bosluk * 0.52, 46)
        oran = min(adim / 12.0, 1.0)
        self._alanlar = []

        for i, (etiket, deger) in enumerate(self.veriler):
            merkez = sol + bosluk * (i + 0.5)
            yuk = (deger / tavan) * alan_y * oran
            x1, x2 = merkez - sutun_g / 2, merkez + sutun_g / 2
            y2 = ust + alan_y
            y1 = y2 - max(yuk, 1)
            yuvarlak_dikdortgen(self, x1, y1, x2, y2, yaricap=min(5, sutun_g / 3),
                                fill=self.renk, outline="")
            self.create_text(merkez, y - alt + 12, text=etiket, fill=tema.YAZI_SOLUK,
                             font=tema.f("govde", 8))
            self._alanlar.append((x1 - 4, x2 + 4, etiket, deger))

    @staticmethod
    def _kisa(deger):
        if deger >= 1_000_000:
            return "{:.1f}M".format(deger / 1_000_000).replace(".", ",")
        if deger >= 1000:
            return "{:.0f}B".format(deger / 1000)
        return "{:.0f}".format(deger)

    def _imlec(self, olay):
        for x1, x2, etiket, deger in getattr(self, "_alanlar", []):
            if x1 <= olay.x <= x2:
                self._ipucu_goster(olay.x, etiket, deger)
                return
        self._ipucu_gizle()

    def _ipucu_goster(self, x, etiket, deger):
        from ..cekirdek.yardimcilar import para
        self.delete("ipucu")
        metin = "{} · {}".format(etiket, para(deger))
        t = self.create_text(0, 0, text=metin, font=tema.f("govde", 8, kalin=True),
                             fill=tema.ZEMIN, tags="ipucu")
        x1, y1, x2, y2 = self.bbox(t)
        gen = x2 - x1
        hx = min(max(x, gen / 2 + 8), self.winfo_width() - gen / 2 - 8)
        self.coords(t, hx, 12)
        kutu = self.create_rectangle(hx - gen / 2 - 6, 3, hx + gen / 2 + 6, 22,
                                     fill=tema.VURGU_ACIK, outline="", tags="ipucu")
        self.tag_lower(kutu, t)

    def _ipucu_gizle(self):
        self.delete("ipucu")


class HalkaGrafik(tk.Canvas):
    def __init__(self, ust, boyut=190, **kw):
        super().__init__(ust, bg=tema.PANEL, width=boyut, height=boyut,
                         highlightthickness=0, bd=0, **kw)
        self.boyut = boyut
        self.veriler = []

    def ciz(self, veriler, orta_ust="", orta_alt=""):
        self.delete("all")
        self.veriler = [(e, d) for e, d in veriler if d > 0]
        toplam = sum(d for _, d in self.veriler)
        b = self.boyut
        dolgu = 14
        if not self.veriler or toplam <= 0:
            self.create_oval(dolgu, dolgu, b - dolgu, b - dolgu, outline=tema.KENAR, width=22)
            self.create_text(b / 2, b / 2, text="veri yok", fill=tema.YAZI_PASIF,
                             font=tema.f("govde", 9))
            return
        baslangic = 90.0
        for i, (etiket, deger) in enumerate(self.veriler):
            yay = 360.0 * deger / toplam
            self.create_arc(dolgu, dolgu, b - dolgu, b - dolgu, start=baslangic,
                            extent=-max(yay, 0.6), style="arc", width=22,
                            outline=tema.GRAFIK_RENK[i % len(tema.GRAFIK_RENK)])
            baslangic -= yay
        if orta_ust:
            self.create_text(b / 2, b / 2 - 8, text=orta_ust, fill=tema.YAZI,
                             font=tema.f("baslik", 13, kalin=True))
        if orta_alt:
            self.create_text(b / 2, b / 2 + 10, text=orta_alt, fill=tema.YAZI_PASIF,
                             font=tema.f("govde", 8))


def gosterge(ust, veriler, arka=None):
    """Halka grafigin yanina konan renkli aciklama listesi."""
    arka = arka or tema.PANEL
    cerceve = tk.Frame(ust, bg=arka)
    toplam = sum(d for _, d in veriler) or 1
    for i, (etiket, deger) in enumerate(veriler[:7]):
        satir = tk.Frame(cerceve, bg=arka)
        satir.pack(fill="x", pady=3)
        tk.Frame(satir, bg=tema.GRAFIK_RENK[i % len(tema.GRAFIK_RENK)], width=9, height=9).pack(
            side="left", padx=(0, 8))
        tk.Label(satir, text=etiket, bg=arka, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 9), anchor="w").pack(side="left")
        tk.Label(satir, text="%{:.0f}".format(100.0 * deger / toplam), bg=arka,
                 fg=tema.YAZI, font=tema.f("mono", 9, kalin=True)).pack(side="right")
    return cerceve


# --- bildirim ve dialoglar -----------------------------------------------

def bildirim(pencere, metin, tur="basari", sure=2600):
    """Sag ustte belirip kendi kendine kapanan kucuk kutu."""
    renk = {"basari": tema.BASARI, "hata": tema.TEHLIKE,
            "uyari": tema.UYARI, "bilgi": tema.BILGI}.get(tur, tema.VURGU)
    kok = pencere.winfo_toplevel()
    kutu = tk.Toplevel(kok)
    kutu.overrideredirect(True)
    kutu.attributes("-topmost", True)
    kutu.configure(bg=tema.KENAR)
    ic = tk.Frame(kutu, bg=tema.PANEL_ACIK)
    ic.pack(padx=1, pady=1)
    tk.Frame(ic, bg=renk, width=4).pack(side="left", fill="y")
    tk.Label(ic, text=metin, bg=tema.PANEL_ACIK, fg=tema.YAZI,
             font=tema.f("govde", 10), padx=14, pady=11, justify="left",
             wraplength=340).pack(side="left")
    kutu.update_idletasks()
    x = kok.winfo_rootx() + kok.winfo_width() - kutu.winfo_width() - 24
    y = kok.winfo_rooty() + 74
    kutu.geometry("+{}+{}".format(x, y))

    try:
        kutu.attributes("-alpha", 0.0)
        _soluklastir(kutu, 0.0, 0.96, 0.12, lambda: None)
    except tk.TclError:
        pass

    def kapat():
        if kutu.winfo_exists():
            try:
                _soluklastir(kutu, 0.96, 0.0, -0.16, kutu.destroy)
            except tk.TclError:
                kutu.destroy()

    kutu.after(sure, kapat)
    ic.bind("<Button-1>", lambda e: kapat())
    return kutu


def _soluklastir(pencere, mevcut, hedef, adim, bitince):
    if not pencere.winfo_exists():
        return
    mevcut += adim
    bitti = mevcut >= hedef if adim > 0 else mevcut <= hedef
    pencere.attributes("-alpha", max(0.0, min(mevcut, 1.0)))
    if bitti:
        bitince()
    else:
        pencere.after(16, lambda: _soluklastir(pencere, mevcut, hedef, adim, bitince))


class TemelDialog(tk.Toplevel):
    """Modal pencere iskeleti. Alt sinif govde() ve kaydet() yazar."""

    def __init__(self, ust, baslik, genislik=520, yukseklik=460, alt_yazi=""):
        super().__init__(ust)
        self.sonuc = None
        self.title(baslik)
        self.configure(bg=tema.ZEMIN)
        self.resizable(False, False)
        self.transient(ust.winfo_toplevel())

        baslik_cer = tk.Frame(self, bg=tema.PANEL_KOYU)
        baslik_cer.pack(fill="x")
        ic = tk.Frame(baslik_cer, bg=tema.PANEL_KOYU)
        ic.pack(fill="x", padx=22, pady=(16, 14))
        tk.Label(ic, text=baslik, bg=tema.PANEL_KOYU, fg=tema.YAZI,
                 font=tema.f("baslik", 15, kalin=True)).pack(side="left")
        if alt_yazi:
            tk.Label(ic, text=alt_yazi, bg=tema.PANEL_KOYU, fg=tema.YAZI_PASIF,
                     font=tema.f("mono", 9)).pack(side="right")
        tk.Frame(self, bg=tema.VURGU, height=2).pack(fill="x")

        self.govde_cer = tk.Frame(self, bg=tema.ZEMIN)
        self.govde_cer.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Frame(self, bg=tema.KENAR, height=1).pack(fill="x")
        self.ayak = tk.Frame(self, bg=tema.PANEL_KOYU)
        self.ayak.pack(fill="x")
        self.dugmeler = tk.Frame(self.ayak, bg=tema.PANEL_KOYU)
        self.dugmeler.pack(side="right", padx=22, pady=14)

        self.govde(self.govde_cer)
        self.dugmeleri_ekle()

        self.update_idletasks()
        self._ortala(ust, genislik, yukseklik)
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.focus_force()

    def _ortala(self, ust, genislik, yukseklik):
        kok = ust.winfo_toplevel()
        gercek_y = max(self.winfo_reqheight(), 120)
        yukseklik = min(max(yukseklik, gercek_y), self.winfo_screenheight() - 80)
        x = kok.winfo_rootx() + (kok.winfo_width() - genislik) // 2
        y = kok.winfo_rooty() + (kok.winfo_height() - yukseklik) // 3
        self.geometry("{}x{}+{}+{}".format(genislik, yukseklik, max(x, 0), max(y, 0)))

    def govde(self, ust):
        raise NotImplementedError

    def dugmeleri_ekle(self):
        Buton(self.dugmeler, "Kaydet", self._kaydet_sar, "birincil", genislik=104).pack(
            side="right", padx=(8, 0))
        Buton(self.dugmeler, "İptal", self.destroy, "ikincil", genislik=88).pack(side="right")

    def _kaydet_sar(self):
        from ..cekirdek.servisler import IsKurali
        try:
            if self.kaydet() is not False:
                self.destroy()
        except IsKurali as h:
            uyari_kutusu(self, "Eksik bilgi", str(h))
        except Exception as h:  # beklenmedik hatayi kullaniciya duz gosteriyoruz
            uyari_kutusu(self, "Hata", "İşlem tamamlanamadı:\n{}".format(h))

    def kaydet(self):
        return True


class _MesajKutusu(TemelDialog):
    def __init__(self, ust, baslik, mesaj, tur="uyari", onayli=False, onay_metni="Evet"):
        self.mesaj = mesaj
        self.tur = tur
        self.onayli = onayli
        self.onay_metni = onay_metni
        self.sonuc = False
        super().__init__(ust, baslik, genislik=440, yukseklik=210)

    def govde(self, ust):
        renk = {"uyari": tema.UYARI, "hata": tema.TEHLIKE,
                "bilgi": tema.BILGI, "soru": tema.VURGU}.get(self.tur, tema.UYARI)
        ikon = {"uyari": "!", "hata": "✕", "bilgi": "i", "soru": "?"}.get(self.tur, "!")
        satir = tk.Frame(ust, bg=tema.ZEMIN)
        satir.pack(fill="both", expand=True)
        yuvarlak = tk.Label(satir, text=ikon, bg=tema.PANEL, fg=renk,
                            font=tema.f("baslik", 17, kalin=True), width=3, height=1)
        yuvarlak.pack(side="left", padx=(0, 16), anchor="n", pady=2)
        tk.Label(satir, text=self.mesaj, bg=tema.ZEMIN, fg=tema.YAZI,
                 font=tema.f("govde", 10), justify="left", anchor="nw",
                 wraplength=310).pack(side="left", fill="both", expand=True)

    def dugmeleri_ekle(self):
        if self.onayli:
            tur = "tehlike" if self.tur in ("uyari", "hata") else "birincil"
            Buton(self.dugmeler, self.onay_metni, self._onayla, tur, genislik=104).pack(
                side="right", padx=(8, 0))
            Buton(self.dugmeler, "Vazgeç", self.destroy, "ikincil", genislik=88).pack(side="right")
        else:
            Buton(self.dugmeler, "Tamam", self.destroy, "birincil", genislik=96).pack(side="right")

    def _onayla(self):
        self.sonuc = True
        self.destroy()


def uyari_kutusu(ust, baslik, mesaj, tur="uyari"):
    kutu = _MesajKutusu(ust, baslik, mesaj, tur)
    ust.winfo_toplevel().wait_window(kutu)


def bilgi_kutusu(ust, baslik, mesaj):
    uyari_kutusu(ust, baslik, mesaj, "bilgi")


def onay_kutusu(ust, baslik, mesaj, onay_metni="Evet, sil"):
    kutu = _MesajKutusu(ust, baslik, mesaj, "soru", onayli=True, onay_metni=onay_metni)
    ust.winfo_toplevel().wait_window(kutu)
    return kutu.sonuc


class Avatar(tk.Canvas):
    """Musteri ad-soyad bas harflerinden daire rozet."""

    def __init__(self, ust, metin, boyut=42, renk=None, arka=None, **kw):
        arka = arka or tema.PANEL
        super().__init__(ust, width=boyut, height=boyut, bg=arka,
                         highlightthickness=0, bd=0, **kw)
        renk = renk or tema.GRAFIK_RENK[abs(hash(metin)) % len(tema.GRAFIK_RENK)]
        self.create_oval(1, 1, boyut - 1, boyut - 1, fill=tema.PANEL_ACIK, outline=renk, width=2)
        self.create_text(boyut / 2, boyut / 2 + 1, text=bas_harfler(metin), fill=renk,
                         font=tema.f("baslik", int(boyut / 3.2), kalin=True))
