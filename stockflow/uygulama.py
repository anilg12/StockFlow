# -*- coding: utf-8 -*-
# StockFlow · uygulama giris noktasi
# Anıl Gül · 2025

import sys
import tkinter as tk
import traceback

from . import ACIKLAMA, KURUM, PROJE_TURU, SURUM, UYGULAMA_ADI
from .arayuz import tema
from .arayuz.ana_pencere import AnaPencere
from .arayuz.giris import GirisEkrani
from .cekirdek import demo
from .cekirdek import veritabani as db

GIRIS_BOYUT = (440, 620)
ANA_BOYUT = (1320, 830)
EN_KUCUK = (1120, 700)


class StockFlow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # tema kurulana kadar cirkin gri pencere gorunmesin
        self.title("{} · {}".format(UYGULAMA_ADI, ACIKLAMA))
        tema.hazirla(self)
        tema.stil_kur(self)
        self._ikon_ata()

        db.kur()
        demo.tohumla()  # yalnizca veritabani bossa calisir

        self.aktif_ekran = None
        self.kullanici = None
        self.protocol("WM_DELETE_WINDOW", self.kapat)
        self.report_callback_exception = self._hata_yakala
        self.giris_ekrani()
        self.deiconify()

    def _ikon_ata(self):
        """Basit bir simge cizip pencereye veriyorum, ayri .ico dosyasi tasimaya gerek kalmiyor."""
        try:
            boyut = 64
            simge = tk.PhotoImage(width=boyut, height=boyut)
            simge.put(tema.PANEL_KOYU, to=(0, 0, boyut, boyut))
            sutunlar = [(10, 40, 22, 56, tema.VURGU_KOYU),
                        (26, 26, 38, 56, tema.VURGU),
                        (42, 14, 54, 56, tema.VURGU_ACIK)]
            for x1, y1, x2, y2, renk in sutunlar:
                simge.put(renk, to=(x1, y1, x2, y2))
            self.iconphoto(True, simge)
            self._simge = simge  # cop toplayici almasin
        except tk.TclError:
            pass

    # --- ekran gecisleri --------------------------------------------------

    def _ekrani_degistir(self, yeni, boyut, en_kucuk=None):
        if self.aktif_ekran is not None:
            self.aktif_ekran.destroy()
        self.aktif_ekran = yeni
        yeni.pack(fill="both", expand=True)
        self.minsize(*(en_kucuk or (200, 200)))
        self._ortala(*boyut)

    def giris_ekrani(self):
        self.kullanici = None
        self.resizable(False, False)
        self._ekrani_degistir(GirisEkrani(self, self.oturum_ac), GIRIS_BOYUT)

    def oturum_ac(self, kullanici):
        self.kullanici = kullanici
        self.resizable(True, True)
        self._ekrani_degistir(AnaPencere(self, kullanici, self.oturum_kapat),
                              ANA_BOYUT, EN_KUCUK)
        self.title("{} · {} · {} {}".format(UYGULAMA_ADI, kullanici["ad_soyad"],
                                            KURUM, PROJE_TURU))

    def oturum_kapat(self):
        from .arayuz.bilesenler import onay_kutusu
        if not onay_kutusu(self, "Oturumu kapat", "Oturumu kapatmak istiyor musunuz?",
                           "Evet, çıkış yap"):
            return
        self.title("{} · {}".format(UYGULAMA_ADI, ACIKLAMA))
        self.giris_ekrani()

    def _ortala(self, genislik, yukseklik):
        ekran_g = self.winfo_screenwidth()
        ekran_y = self.winfo_screenheight()
        genislik = min(genislik, ekran_g - 60)
        yukseklik = min(yukseklik, ekran_y - 80)
        x = (ekran_g - genislik) // 2
        y = max((ekran_y - yukseklik) // 2 - 20, 0)
        self.geometry("{}x{}+{}+{}".format(genislik, yukseklik, x, y))

    # --- hata / kapanis ---------------------------------------------------

    def _hata_yakala(self, tur, deger, iz):
        """Tkinter geri cagrimlarindaki hatalar sessizce yutulmasin."""
        metin = "".join(traceback.format_exception(tur, deger, iz))
        sys.stderr.write(metin)
        try:
            from .arayuz.bilesenler import uyari_kutusu
            uyari_kutusu(self, "Beklenmeyen hata",
                         "{}\n\nAyrıntı konsola yazıldı.".format(deger), "hata")
        except Exception:
            pass

    def kapat(self):
        db.kapat()
        self.destroy()


def calistir():
    if sys.version_info < (3, 8):
        print("StockFlow için Python 3.8 veya üzeri gerekiyor.")
        return 1
    uygulama = StockFlow()
    uygulama.mainloop()
    return 0
