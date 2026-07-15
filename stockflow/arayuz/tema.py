# -*- coding: utf-8 -*-
# StockFlow · renk paleti, font secimi ve ttk stilleri
# Anıl Gül · 2025

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --- palet ---------------------------------------------------------------
ZEMIN       = "#0C1017"   # pencere arka plani
PANEL       = "#141A24"   # kart / panel yuzeyi
PANEL_ACIK  = "#1C2431"   # hover, secili satir
PANEL_KOYU  = "#0A0E14"   # kenar cubugu
KENAR       = "#26313F"
KENAR_ACIK  = "#33404F"

YAZI        = "#E7EDF4"
YAZI_SOLUK  = "#8695A8"
YAZI_PASIF  = "#57657A"

VURGU       = "#00BFA6"   # ana vurgu
VURGU_ACIK  = "#26E0C4"
VURGU_KOYU  = "#00907C"
VURGU_ISIK  = "#12312E"   # vurgunun cok soluk zemin hali

BASARI      = "#3FB950"
UYARI       = "#E3A73C"
TEHLIKE     = "#EF5350"
BILGI       = "#4C8DFF"
MOR         = "#A371F7"

ZEBRA       = "#111721"

GRAFIK_RENK = [VURGU, BILGI, MOR, UYARI, BASARI, TEHLIKE, "#F778BA", "#56D4DD"]

# Fontlar sistemde varsa kullanilir, yoksa listedeki bir sonrakine duser.
_BASLIK_ADAY = ["Bahnschrift SemiBold", "Bahnschrift", "Segoe UI Semibold",
                "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Liberation Sans"]
_GOVDE_ADAY  = ["Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans", "Liberation Sans"]
_MONO_ADAY   = ["Consolas", "Cascadia Mono", "Menlo", "DejaVu Sans Mono", "Liberation Mono"]

BASLIK_AILE = "TkDefaultFont"
GOVDE_AILE  = "TkDefaultFont"
MONO_AILE   = "TkFixedFont"


def _ilk_bulunan(adaylar, mevcut):
    for ad in adaylar:
        if ad.lower() in mevcut:
            return ad
    return adaylar[-1]


def hazirla(kok):
    """Tk kokü olustuktan sonra bir kez cagrilir."""
    global BASLIK_AILE, GOVDE_AILE, MONO_AILE
    mevcut = {a.lower() for a in tkfont.families(kok)}
    BASLIK_AILE = _ilk_bulunan(_BASLIK_ADAY, mevcut)
    GOVDE_AILE = _ilk_bulunan(_GOVDE_ADAY, mevcut)
    MONO_AILE = _ilk_bulunan(_MONO_ADAY, mevcut)


def f(tur="govde", boyut=10, kalin=False, egik=False):
    aile = {"baslik": BASLIK_AILE, "govde": GOVDE_AILE, "mono": MONO_AILE}.get(tur, GOVDE_AILE)
    stil = []
    if kalin:
        stil.append("bold")
    if egik:
        stil.append("italic")
    return (aile, boyut, " ".join(stil)) if stil else (aile, boyut)


def stil_kur(kok):
    stil = ttk.Style(kok)
    stil.theme_use("clam")  # clam disindaki temalar arka plan rengini yok sayiyor

    kok.configure(bg=ZEMIN)
    kok.option_add("*Background", ZEMIN)
    kok.option_add("*Foreground", YAZI)
    kok.option_add("*selectBackground", VURGU)
    kok.option_add("*selectForeground", ZEMIN)
    kok.option_add("*insertBackground", VURGU)
    # Combobox acilan listesi ttk stiline uymuyor, ayrica ayarlanmasi gerekiyor.
    kok.option_add("*TCombobox*Listbox.background", PANEL_ACIK)
    kok.option_add("*TCombobox*Listbox.foreground", YAZI)
    kok.option_add("*TCombobox*Listbox.selectBackground", VURGU)
    kok.option_add("*TCombobox*Listbox.selectForeground", ZEMIN)
    kok.option_add("*TCombobox*Listbox.font", f("govde", 10))
    kok.option_add("*TCombobox*Listbox.borderWidth", 0)

    # --- Treeview
    stil.configure("Treeview",
                   background=PANEL,
                   fieldbackground=PANEL,
                   foreground=YAZI,
                   bordercolor=KENAR,
                   borderwidth=0,
                   rowheight=30,
                   font=f("govde", 10))
    stil.map("Treeview",
             background=[("selected", VURGU_ISIK)],
             foreground=[("selected", VURGU_ACIK)])
    stil.configure("Treeview.Heading",
                   background=PANEL_ACIK,
                   foreground=YAZI_SOLUK,
                   relief="flat",
                   borderwidth=0,
                   padding=(10, 8),
                   font=f("govde", 9, kalin=True))
    stil.map("Treeview.Heading",
             background=[("active", KENAR)],
             foreground=[("active", VURGU_ACIK)])
    stil.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # --- Scrollbar (ok tuslarini kaldirdim, ince ve sade dursun)
    for yon in ("Vertical", "Horizontal"):
        stil.layout("SF.{}.TScrollbar".format(yon), [
            ("{}.Scrollbar.trough".format(yon), {
                "sticky": "nswe",
                "children": [("{}.Scrollbar.thumb".format(yon),
                              {"expand": "1", "sticky": "nswe"})],
            }),
        ])
        stil.configure("SF.{}.TScrollbar".format(yon),
                       background=KENAR,
                       troughcolor=ZEMIN,
                       bordercolor=ZEMIN,
                       darkcolor=KENAR,
                       lightcolor=KENAR,
                       arrowcolor=YAZI_SOLUK,
                       borderwidth=0,
                       relief="flat",
                       width=10)
        stil.map("SF.{}.TScrollbar".format(yon),
                 background=[("active", KENAR_ACIK), ("pressed", VURGU_KOYU)])

    # --- Entry
    stil.configure("SF.TEntry",
                   fieldbackground=PANEL_ACIK,
                   background=PANEL_ACIK,
                   foreground=YAZI,
                   bordercolor=KENAR,
                   lightcolor=KENAR,
                   darkcolor=KENAR,
                   insertcolor=VURGU,
                   borderwidth=1,
                   relief="flat",
                   padding=(8, 7))
    stil.map("SF.TEntry",
             bordercolor=[("focus", VURGU)],
             lightcolor=[("focus", VURGU)],
             darkcolor=[("focus", VURGU)])

    # --- Combobox
    stil.configure("SF.TCombobox",
                   fieldbackground=PANEL_ACIK,
                   background=PANEL_ACIK,
                   foreground=YAZI,
                   arrowcolor=YAZI_SOLUK,
                   bordercolor=KENAR,
                   lightcolor=KENAR,
                   darkcolor=KENAR,
                   selectbackground=PANEL_ACIK,
                   selectforeground=YAZI,
                   borderwidth=1,
                   relief="flat",
                   padding=(8, 6))
    stil.map("SF.TCombobox",
             fieldbackground=[("readonly", PANEL_ACIK), ("disabled", PANEL)],
             foreground=[("disabled", YAZI_PASIF)],
             bordercolor=[("focus", VURGU), ("hover", KENAR_ACIK)],
             lightcolor=[("focus", VURGU)],
             darkcolor=[("focus", VURGU)],
             arrowcolor=[("hover", VURGU_ACIK)])

    # --- Notebook (musteri detay sekmeleri)
    stil.configure("SF.TNotebook", background=PANEL, borderwidth=0, tabmargins=(0, 0, 0, 0))
    stil.configure("SF.TNotebook.Tab",
                   background=PANEL,
                   foreground=YAZI_SOLUK,
                   padding=(18, 9),
                   borderwidth=0,
                   font=f("govde", 10, kalin=True))
    stil.map("SF.TNotebook.Tab",
             background=[("selected", PANEL), ("active", PANEL_ACIK)],
             foreground=[("selected", VURGU_ACIK), ("active", YAZI)])

    # --- Checkbutton
    stil.configure("SF.TCheckbutton",
                   background=PANEL,
                   foreground=YAZI,
                   indicatorcolor=PANEL_ACIK,
                   indicatorbackground=PANEL_ACIK,
                   focuscolor=PANEL,
                   font=f("govde", 10))
    stil.map("SF.TCheckbutton",
             indicatorcolor=[("selected", VURGU), ("active", KENAR_ACIK)],
             background=[("active", PANEL)],
             foreground=[("active", VURGU_ACIK)])

    # --- Progressbar (rapor ekraninda oran cubugu)
    stil.configure("SF.Horizontal.TProgressbar",
                   background=VURGU,
                   troughcolor=PANEL_ACIK,
                   bordercolor=PANEL_ACIK,
                   lightcolor=VURGU,
                   darkcolor=VURGU,
                   borderwidth=0,
                   thickness=6)

    stil.configure("SF.TSeparator", background=KENAR)
    return stil


def renk_karistir(a, b, oran):
    """Iki hex rengi arasinda dogrusal gecis. Hover animasyonlarinda lazim."""
    a = a.lstrip("#")
    b = b.lstrip("#")
    kanal = []
    for i in (0, 2, 4):
        x = int(a[i:i + 2], 16)
        y = int(b[i:i + 2], 16)
        kanal.append(int(round(x + (y - x) * oran)))
    return "#{:02X}{:02X}{:02X}".format(*kanal)
