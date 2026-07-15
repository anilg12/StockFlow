# -*- coding: utf-8 -*-
# StockFlow · satis fisi sayfasi
# Anıl Gül · 2025

import tkinter as tk
from tkinter import filedialog

from .. import tema
from ..ana_pencere import Sayfa
from ..bilesenler import (Alan, AramaKutusu, Buton, CokSatir, Rozet, Secim,
                          Tablo, TarihGirisi, TemelDialog, onay_kutusu,
                          uyari_kutusu)
from ...cekirdek import servisler as srv
from ...cekirdek import veritabani as db
from ...cekirdek.yardimcilar import (ay_basi, bugun, csv_yaz, gun_ekle, kisalt,
                                     ondalik, para, sayi, tr_tarih)

ARALIKLAR = ["Bu ay", "Geçen ay", "Son 7 gün", "Son 30 gün", "Son 90 gün", "Tümü"]


def aralik_coz(secim):
    b = bugun()
    if secim == "Bu ay":
        return ay_basi(0), b
    if secim == "Geçen ay":
        bas = ay_basi(-1)
        return bas, gun_ekle(ay_basi(0), -1)
    if secim == "Son 7 gün":
        return gun_ekle(b, -7), b
    if secim == "Son 30 gün":
        return gun_ekle(b, -30), b
    if secim == "Son 90 gün":
        return gun_ekle(b, -90), b
    return "1900-01-01", "2999-12-31"


class SatisSayfasi(Sayfa):
    BASLIK = "Satışlar"
    ALT_BASLIK = "Fiş kayıtları, yeni satış girişi ve iptal işlemleri"

    def kur(self):
        self.arama_metni = ""
        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.pack(fill="both", expand=True, padx=24, pady=(18, 24))

        arac = tk.Frame(kabuk, bg=tema.ZEMIN)
        arac.pack(fill="x", pady=(0, 12))
        self.arama = AramaKutusu(arac, self._ara, "Fiş no veya müşteri ara", genislik=26)
        self.arama.pack(side="left")
        self.aralik = Secim(arac, "", ARALIKLAR, "Son 30 gün", genislik=12,
                            degisince=lambda v: self.yenile())
        self.aralik.pack(side="left", padx=(10, 0))
        self.odeme = Secim(arac, "", ["Tümü"] + srv.ODEME_TURLERI, "Tümü", genislik=13,
                           degisince=lambda v: self.yenile())
        self.odeme.pack(side="left", padx=(8, 0))

        Buton(arac, "Yeni Satış", self.yeni_satis, "birincil", genislik=118, ikon="+").pack(
            side="right")
        Buton(arac, "Fiş Detayı", self.detay, "ikincil", genislik=100).pack(side="right", padx=6)
        Buton(arac, "CSV", self.disa_aktar, "sade", genislik=64).pack(side="right")
        Buton(arac, "İptal Et", self.iptal, "sade", genislik=80).pack(side="right", padx=6)

        cerceve = tk.Frame(kabuk, bg=tema.PANEL, highlightbackground=tema.KENAR,
                           highlightthickness=1)
        cerceve.pack(fill="both", expand=True)
        self.tablo = Tablo(cerceve, [
            ("fis", "Fiş No", 120, "w"),
            ("tarih", "Tarih", 95, "center"),
            ("musteri", "Müşteri", 260, "w"),
            ("kalem", "Kalem", 65, "center"),
            ("ara", "Ara Toplam", 110, "e"),
            ("iskonto", "İskonto", 95, "e"),
            ("kdv", "KDV", 95, "e"),
            ("toplam", "Genel Toplam", 120, "e"),
            ("odeme", "Ödeme", 105, "center"),
        ], yukseklik=16, cift_tik=self.detay)
        self.tablo.pack(fill="both", expand=True, padx=1, pady=1)

        alt = tk.Frame(kabuk, bg=tema.ZEMIN)
        alt.pack(fill="x", pady=(10, 0))
        self.sayac = tk.Label(alt, text="", bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                              font=tema.f("govde", 9), anchor="w")
        self.sayac.pack(side="left")
        self.toplam_etiketi = tk.Label(alt, text="", bg=tema.ZEMIN, fg=tema.YAZI,
                                       font=tema.f("mono", 9, kalin=True), anchor="e")
        self.toplam_etiketi.pack(side="right")

    def _ara(self, metin):
        self.arama_metni = metin
        self.yenile()

    def yenile(self):
        bas, bit = aralik_coz(self.aralik.al())
        kayitlar = srv.satislar(bas, bit, self.arama_metni, self.odeme.al())
        satirlar = []
        for s in kayitlar:
            kalem = db.deger("SELECT COUNT(*) FROM satis_kalemleri WHERE satis_id = ?", (s["id"],))
            satirlar.append((s["id"], (
                s["fis_no"], tr_tarih(s["tarih"]), kisalt(s["musteri_unvan"], 32),
                str(kalem), para(s["ara_toplam"], False), para(s["iskonto"], False),
                para(s["kdv"], False), para(s["toplam"], False), s["odeme_turu"],
            )))
        self.tablo.doldur(satirlar, lambda k, d: "uyari" if d[8] == "Veresiye" else None)
        toplam = sum(s["toplam"] for s in kayitlar)
        self.sayac.configure(text="{} fiş listeleniyor · ortalama sepet {}".format(
            len(kayitlar), para(toplam / len(kayitlar) if kayitlar else 0)))
        self.toplam_etiketi.configure(text="Dönem cirosu {}".format(para(toplam)))

    # --- islemler ---------------------------------------------------------

    def yeni_satis(self):
        if not srv.urunler(sadece_aktif=True):
            uyari_kutusu(self, "Ürün yok", "Satış yapabilmek için önce stok kartı eklemelisiniz.")
            return
        pencere = YeniSatisDialog(self, self.kabuk.kullanici)
        self.wait_window(pencere)
        if pencere.sonuc:
            self.yenile()
            for sayfa in ("panel", "stok", "musteri"):
                self.kabuk.sayfayi_tazele(sayfa)
            self.kabuk.rozetleri_yenile()
            self.bildir("Fiş kaydedildi: {}".format(pencere.sonuc))

    def detay(self):
        kimlik = self.tablo.secili_kimlik()
        if not kimlik:
            uyari_kutusu(self, "Seçim yok", "Detayını görmek için bir fiş seçin.")
            return
        FisDetayDialog(self, int(kimlik))

    def iptal(self):
        kimlik = self.tablo.secili_kimlik()
        if not kimlik:
            uyari_kutusu(self, "Seçim yok", "İptal etmek için bir fiş seçin.")
            return
        fis = srv.satis(int(kimlik))
        mesaj = ("{} numaralı fiş iptal edilecek.\n\n"
                 "Fişteki ürünlerin stoğu geri yüklenecek"
                 "{}.\n\nBu işlem geri alınamaz.").format(
            fis["fis_no"],
            " ve müşteri bakiyesinden {} düşülecek".format(para(fis["toplam"]))
            if fis["odeme_turu"] == "Veresiye" else "")
        if not onay_kutusu(self, "Fişi iptal et", mesaj, "Evet, iptal et"):
            return
        srv.satis_iptal(int(kimlik))
        self.yenile()
        for sayfa in ("panel", "stok", "musteri"):
            self.kabuk.sayfayi_tazele(sayfa)
        self.kabuk.rozetleri_yenile()
        self.bildir("Fiş iptal edildi, stok geri yüklendi.", "uyari")

    def disa_aktar(self):
        satirlar = self.tablo.gorunen_veri()
        if not satirlar:
            uyari_kutusu(self, "Boş liste", "Dışa aktarılacak fiş yok.")
            return
        yol = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", initialfile="satislar.csv",
            filetypes=[("CSV dosyası", "*.csv")])
        if not yol:
            return
        csv_yaz(yol, [k[1] for k in self.tablo.kolonlar], satirlar)
        self.bildir("{} satır dışa aktarıldı.".format(len(satirlar)))


class YeniSatisDialog(TemelDialog):
    def __init__(self, ust, kullanici):
        self.kullanici = kullanici
        self.sepet = []
        self.fis_no = srv.fis_no_uret()
        self.urun_haritasi = {}
        super().__init__(ust, "Yeni Satış Fişi", genislik=880, yukseklik=680,
                         alt_yazi=self.fis_no)

    def govde(self, ust):
        # --- baslik alanlari
        bas = tk.Frame(ust, bg=tema.ZEMIN)
        bas.pack(fill="x")
        for i in range(3):
            bas.columnconfigure(i, weight=1, uniform="b")

        musteriler = srv.musteriler(sadece_aktif=True)
        self.musteri_haritasi = {"Perakende Satış (müşterisiz)": None}
        for m in musteriler:
            self.musteri_haritasi["{} · {}".format(m["unvan"], m["kod"])] = m["id"]
        self.musteri = Secim(bas, "MÜŞTERİ", list(self.musteri_haritasi.keys()),
                             "Perakende Satış (müşterisiz)", arka=tema.ZEMIN)
        self.musteri.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self.tarih = TarihGirisi(bas, "TARİH", bugun(), arka=tema.ZEMIN)
        self.tarih.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # --- urun ekleme satiri
        tk.Frame(ust, bg=tema.KENAR, height=1).pack(fill="x", pady=14)
        ekle = tk.Frame(ust, bg=tema.ZEMIN)
        ekle.pack(fill="x")
        ekle.columnconfigure(0, weight=4)
        for i in (1, 2, 3):
            ekle.columnconfigure(i, weight=1)

        for u in srv.urunler(sadece_aktif=True):
            etiket = "{} · {} (stok {:g})".format(u["kod"], u["ad"], u["stok"])
            self.urun_haritasi[etiket] = u
        self.urun = Secim(ekle, "ÜRÜN", list(self.urun_haritasi.keys()), "", arka=tema.ZEMIN,
                          degisince=lambda v: self._urun_secildi())
        self.urun.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.miktar = Alan(ekle, "MİKTAR", "1", genislik=8, arka=tema.ZEMIN)
        self.miktar.grid(row=0, column=1, sticky="ew", padx=6)
        self.fiyat = Alan(ekle, "BİRİM FİYAT", "0,00", genislik=10, arka=tema.ZEMIN)
        self.fiyat.grid(row=0, column=2, sticky="ew", padx=6)
        self.iskonto = Alan(ekle, "İSKONTO %", "0", genislik=8, arka=tema.ZEMIN)
        self.iskonto.grid(row=0, column=3, sticky="ew", padx=(6, 8))
        dugme_cer = tk.Frame(ekle, bg=tema.ZEMIN)
        dugme_cer.grid(row=0, column=4, sticky="e")
        tk.Label(dugme_cer, text=" ", bg=tema.ZEMIN, font=tema.f("govde", 9)).pack()
        Buton(dugme_cer, "Sepete Ekle", self._sepete_ekle, "birincil", genislik=116).pack()
        self._urun_secildi()

        # --- sepet
        alt = tk.Frame(ust, bg=tema.ZEMIN)
        alt.pack(fill="both", expand=True, pady=(14, 0))
        alt.columnconfigure(0, weight=3, uniform="s")
        alt.columnconfigure(1, weight=1, uniform="s")
        alt.rowconfigure(0, weight=1)

        sepet_cer = tk.Frame(alt, bg=tema.PANEL, highlightbackground=tema.KENAR,
                             highlightthickness=1)
        sepet_cer.grid(row=0, column=0, sticky="nsew")
        self.tablo = Tablo(sepet_cer, [
            ("kod", "Kod", 88, "w"),
            ("ad", "Ürün", 230, "w"),
            ("miktar", "Miktar", 70, "e"),
            ("fiyat", "B.Fiyat", 90, "e"),
            ("isk", "İsk.%", 55, "e"),
            ("tutar", "Tutar", 100, "e"),
        ], yukseklik=9)
        self.tablo.pack(fill="both", expand=True, padx=1, pady=1)
        self.tablo.agac.bind("<Delete>", lambda e: self._satir_sil())

        # --- ozet
        ozet = tk.Frame(alt, bg=tema.PANEL, highlightbackground=tema.KENAR, highlightthickness=1)
        ozet.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        ic = tk.Frame(ozet, bg=tema.PANEL)
        ic.pack(fill="both", expand=True, padx=16, pady=14)

        self.ozet_etiketleri = {}
        for anahtar, metin in (("ara", "Ara Toplam"), ("isk", "İskonto"), ("net", "Net Tutar"),
                               ("kdv", "KDV (%{})".format(db.ayar("kdv_orani", "20")))):
            satir = tk.Frame(ic, bg=tema.PANEL)
            satir.pack(fill="x", pady=3)
            tk.Label(satir, text=metin, bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9), anchor="w").pack(side="left")
            e = tk.Label(satir, text="0,00 ₺", bg=tema.PANEL, fg=tema.YAZI,
                         font=tema.f("mono", 9), anchor="e")
            e.pack(side="right")
            self.ozet_etiketleri[anahtar] = e

        tk.Frame(ic, bg=tema.KENAR, height=1).pack(fill="x", pady=9)
        tk.Label(ic, text="GENEL TOPLAM", bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                 font=tema.f("govde", 8, kalin=True), anchor="w").pack(fill="x")
        self.toplam_etiketi = tk.Label(ic, text="0,00 ₺", bg=tema.PANEL, fg=tema.VURGU_ACIK,
                                       font=tema.f("baslik", 19, kalin=True), anchor="w")
        self.toplam_etiketi.pack(fill="x", pady=(2, 10))

        self.odeme = Secim(ic, "ÖDEME TÜRÜ", srv.ODEME_TURLERI, "Nakit",
                           degisince=lambda v: self._odeme_uyarisi())
        self.odeme.pack(fill="x")
        self.odeme_uyari = tk.Label(ic, text="", bg=tema.PANEL, fg=tema.UYARI,
                                    font=tema.f("govde", 8), anchor="w", wraplength=180,
                                    justify="left")
        self.odeme_uyari.pack(fill="x", pady=(4, 0))
        self.notlar = CokSatir(ic, "NOT", "", satir=3)
        self.notlar.pack(fill="both", expand=True, pady=(10, 0))
        Buton(ic, "Seçili Satırı Çıkar", self._satir_sil, "sade", yukseklik=30).pack(
            fill="x", pady=(10, 0))
        self._hesapla()

    def _urun_secildi(self):
        u = self.urun_haritasi.get(self.urun.al())
        if u:
            self.fiyat.yaz(para(u["satis_fiyati"], False))

    def _sepete_ekle(self):
        u = self.urun_haritasi.get(self.urun.al())
        if not u:
            uyari_kutusu(self, "Ürün seçilmedi", "Listeden bir ürün seçin.")
            return
        miktar = ondalik(self.miktar.al())
        if miktar <= 0:
            uyari_kutusu(self, "Geçersiz miktar", "Miktar sıfırdan büyük olmalı.")
            return
        sepetteki = sum(k["miktar"] for k in self.sepet if k["urun_id"] == u["id"])
        if sepetteki + miktar > u["stok"]:
            uyari_kutusu(self, "Stok yetersiz",
                         "'{}' için mevcut stok {:g}. Sepette zaten {:g} adet var.".format(
                             u["ad"], u["stok"], sepetteki))
            return
        iskonto = max(0.0, min(ondalik(self.iskonto.al()), 100.0))
        self.sepet.append({
            "urun_id": u["id"],
            "kod": u["kod"],
            "ad": u["ad"],
            "miktar": miktar,
            "birim_fiyat": ondalik(self.fiyat.al()),
            "iskonto": iskonto,
        })
        self.miktar.yaz("1")
        self.iskonto.yaz("0")
        self._sepeti_ciz()
        self._hesapla()

    def _satir_sil(self):
        kimlik = self.tablo.secili_kimlik()
        if kimlik is None:
            return
        indeks = int(kimlik)
        if 0 <= indeks < len(self.sepet):
            self.sepet.pop(indeks)
            self._sepeti_ciz()
            self._hesapla()

    def _sepeti_ciz(self):
        self.tablo.doldur([
            (i, (k["kod"], kisalt(k["ad"], 30), sayi(k["miktar"]),
                 para(k["birim_fiyat"], False), "{:g}".format(k["iskonto"]),
                 para(k["miktar"] * k["birim_fiyat"] * (1 - k["iskonto"] / 100), False)))
            for i, k in enumerate(self.sepet)
        ], lambda k, d: "basari" if float(d[4]) > 0 else None)

    def _hesapla(self):
        ara = sum(k["miktar"] * k["birim_fiyat"] for k in self.sepet)
        isk = sum(k["miktar"] * k["birim_fiyat"] * k["iskonto"] / 100 for k in self.sepet)
        net = ara - isk
        kdv = net * float(db.ayar("kdv_orani", "20") or 20) / 100
        self.ozet_etiketleri["ara"].configure(text=para(ara))
        self.ozet_etiketleri["isk"].configure(text="-" + para(isk) if isk else para(0),
                                              fg=tema.UYARI if isk else tema.YAZI)
        self.ozet_etiketleri["net"].configure(text=para(net))
        self.ozet_etiketleri["kdv"].configure(text=para(kdv))
        self.toplam_etiketi.configure(text=para(net + kdv))

    def _odeme_uyarisi(self):
        if self.odeme.al() == "Veresiye":
            if self.musteri_haritasi.get(self.musteri.al()) is None:
                self.odeme_uyari.configure(
                    text="Veresiye için müşteri seçmelisiniz.", fg=tema.TEHLIKE)
            else:
                self.odeme_uyari.configure(
                    text="Tutar müşteri bakiyesine borç olarak işlenecek.", fg=tema.UYARI)
        else:
            self.odeme_uyari.configure(text="")

    def dugmeleri_ekle(self):
        Buton(self.dugmeler, "Fişi Kaydet", self._kaydet_sar, "birincil", genislik=124).pack(
            side="right", padx=(8, 0))
        Buton(self.dugmeler, "İptal", self.destroy, "ikincil", genislik=88).pack(side="right")

    def kaydet(self):
        musteri_id = self.musteri_haritasi.get(self.musteri.al())
        if self.odeme.al() == "Veresiye" and musteri_id is None:
            raise srv.IsKurali("Veresiye satış için müşteri seçilmeli.")
        kimlik = srv.satis_kaydet({
            "fis_no": self.fis_no,
            "musteri_id": musteri_id,
            "tarih": self.tarih.al() or bugun(),
            "odeme_turu": self.odeme.al(),
            "notlar": self.notlar.al(),
            "kullanici_id": self.kullanici["id"],
        }, [{"urun_id": k["urun_id"], "miktar": k["miktar"],
             "birim_fiyat": k["birim_fiyat"], "iskonto": k["iskonto"]} for k in self.sepet])
        self.sonuc = srv.satis(kimlik)["fis_no"]
        return True


class FisDetayDialog(TemelDialog):
    def __init__(self, ust, satis_id):
        self.fis = srv.satis(satis_id)
        self.kalemler = srv.satis_kalemleri(satis_id)
        super().__init__(ust, "Fiş Detayı", genislik=680, yukseklik=560,
                         alt_yazi=self.fis["fis_no"])

    def govde(self, ust):
        f = self.fis
        bas = tk.Frame(ust, bg=tema.PANEL, highlightbackground=tema.KENAR, highlightthickness=1)
        bas.pack(fill="x")
        ic = tk.Frame(bas, bg=tema.PANEL)
        ic.pack(fill="x", padx=16, pady=13)
        sol = tk.Frame(ic, bg=tema.PANEL)
        sol.pack(side="left", fill="x", expand=True)
        tk.Label(sol, text=f["musteri_unvan"], bg=tema.PANEL, fg=tema.YAZI,
                 font=tema.f("baslik", 13, kalin=True), anchor="w").pack(fill="x")
        tk.Label(sol, text="{} · {}".format(tr_tarih(f["tarih"]), db.ayar("firma_adi")),
                 bg=tema.PANEL, fg=tema.YAZI_PASIF, font=tema.f("govde", 9),
                 anchor="w").pack(fill="x", pady=(3, 0))
        Rozet(ic, f["odeme_turu"],
              "sari" if f["odeme_turu"] == "Veresiye" else "yesil").pack(side="right")

        tablo_cer = tk.Frame(ust, bg=tema.PANEL, highlightbackground=tema.KENAR,
                             highlightthickness=1)
        tablo_cer.pack(fill="both", expand=True, pady=(14, 0))
        tablo = Tablo(tablo_cer, [
            ("kod", "Kod", 90, "w"),
            ("ad", "Ürün", 230, "w"),
            ("miktar", "Miktar", 70, "e"),
            ("fiyat", "B.Fiyat", 95, "e"),
            ("isk", "İsk.%", 55, "e"),
            ("tutar", "Tutar", 105, "e"),
        ], yukseklik=9)
        tablo.pack(fill="both", expand=True, padx=1, pady=1)
        tablo.doldur([
            (k["id"], (k["urun_kod"], k["urun_ad"], sayi(k["miktar"]),
                       para(k["birim_fiyat"], False), "{:g}".format(k["iskonto"]),
                       para(k["tutar"], False)))
            for k in self.kalemler
        ])

        ozet = tk.Frame(ust, bg=tema.ZEMIN)
        ozet.pack(fill="x", pady=(14, 0))
        sag = tk.Frame(ozet, bg=tema.ZEMIN)
        sag.pack(side="right")
        for metin, deger, renk in (("Ara Toplam", f["ara_toplam"], tema.YAZI_SOLUK),
                                   ("İskonto", -f["iskonto"], tema.UYARI),
                                   ("KDV", f["kdv"], tema.YAZI_SOLUK)):
            satir = tk.Frame(sag, bg=tema.ZEMIN)
            satir.pack(fill="x", pady=2)
            tk.Label(satir, text=metin, bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9), width=14, anchor="w").pack(side="left")
            tk.Label(satir, text=para(deger), bg=tema.ZEMIN, fg=renk,
                     font=tema.f("mono", 9), width=14, anchor="e").pack(side="right")
        tk.Frame(sag, bg=tema.KENAR, height=1).pack(fill="x", pady=6)
        toplam = tk.Frame(sag, bg=tema.ZEMIN)
        toplam.pack(fill="x")
        tk.Label(toplam, text="GENEL TOPLAM", bg=tema.ZEMIN, fg=tema.YAZI,
                 font=tema.f("govde", 9, kalin=True), width=14, anchor="w").pack(side="left")
        tk.Label(toplam, text=para(f["toplam"]), bg=tema.ZEMIN, fg=tema.VURGU_ACIK,
                 font=tema.f("mono", 13, kalin=True), anchor="e").pack(side="right")

        if f["notlar"]:
            tk.Label(ozet, text="Not: " + f["notlar"], bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9), anchor="nw", justify="left",
                     wraplength=280).pack(side="left", fill="x", expand=True)

    def dugmeleri_ekle(self):
        Buton(self.dugmeler, "Kapat", self.destroy, "ikincil", genislik=88).pack(side="right")
        Buton(self.dugmeler, "Metin Olarak Kaydet", self._disa_aktar, "sade",
              genislik=156).pack(side="right", padx=(0, 8))

    def _disa_aktar(self):
        yol = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt",
            initialfile="{}.txt".format(self.fis["fis_no"]),
            filetypes=[("Metin dosyası", "*.txt")])
        if not yol:
            return
        f = self.fis
        cizgi = "-" * 52
        satirlar = [
            db.ayar("firma_adi"),
            db.ayar("firma_adres"),
            "Tel: {}   V.No: {}".format(db.ayar("firma_telefon"), db.ayar("firma_vergi_no")),
            cizgi,
            "FİŞ NO : {}".format(f["fis_no"]),
            "TARİH  : {}".format(tr_tarih(f["tarih"])),
            "MÜŞTERİ: {}".format(f["musteri_unvan"]),
            "ÖDEME  : {}".format(f["odeme_turu"]),
            cizgi,
        ]
        for k in self.kalemler:
            satirlar.append("{:<30.30}".format(k["urun_ad"]))
            satirlar.append("  {:g} x {:>12} {:>14}".format(
                k["miktar"], para(k["birim_fiyat"], False), para(k["tutar"], False)))
        satirlar += [
            cizgi,
            "{:<30}{:>20}".format("ARA TOPLAM", para(f["ara_toplam"], False)),
            "{:<30}{:>20}".format("İSKONTO", "-" + para(f["iskonto"], False)),
            "{:<30}{:>20}".format("KDV", para(f["kdv"], False)),
            "{:<30}{:>20}".format("GENEL TOPLAM", para(f["toplam"], False)),
            cizgi,
            "StockFlow · Anıl Gül · 2025",
        ]
        with open(yol, "w", encoding="utf-8") as dosya:
            dosya.write("\n".join(satirlar))
        self.destroy()
