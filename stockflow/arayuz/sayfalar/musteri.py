# -*- coding: utf-8 -*-
# StockFlow · musteri iliskileri (CRM) sayfasi
# Anıl Gül · 2025

import tkinter as tk
from tkinter import ttk

from .. import tema
from ..ana_pencere import Sayfa
from ..bilesenler import (Alan, AramaKutusu, Avatar, BosDurum, Buton, CokSatir,
                          Rozet, Secim, Tablo, TarihGirisi, TemelDialog,
                          onay_kutusu, uyari_kutusu)
from ...cekirdek import servisler as srv
from ...cekirdek.yardimcilar import (bugun, eposta_gecerli, kisalt, ondalik,
                                     para, sayi, telefon_temizle, tr_tarih)

SEHIRLER = ["Nevşehir", "Kayseri", "Ankara", "İstanbul", "İzmir", "Adana", "Konya",
            "Bursa", "Antalya", "Gaziantep", "Eskişehir", "Samsun", "Trabzon", "Diğer"]


class MusteriSayfasi(Sayfa):
    BASLIK = "Müşteriler"
    ALT_BASLIK = "Müşteri kartları, görüşme geçmişi ve satın alma özeti"

    def kur(self):
        self.arama_metni = ""
        self.secili_id = None

        kabuk = tk.Frame(self, bg=tema.ZEMIN)
        kabuk.pack(fill="both", expand=True, padx=24, pady=(18, 24))
        kabuk.columnconfigure(0, weight=2, uniform="k")
        kabuk.columnconfigure(1, weight=3, uniform="k")
        kabuk.rowconfigure(0, weight=1)

        # --- sol: liste
        sol = tk.Frame(kabuk, bg=tema.ZEMIN)
        sol.grid(row=0, column=0, sticky="nsew")

        arac = tk.Frame(sol, bg=tema.ZEMIN)
        arac.pack(fill="x", pady=(0, 10))
        self.arama = AramaKutusu(arac, self._ara, "Müşteri ara", genislik=22)
        self.arama.pack(side="left")
        self.tip = Secim(arac, "", ["Tümü", "Bireysel", "Kurumsal"], "Tümü", genislik=10,
                         degisince=lambda v: self.yenile())
        self.tip.pack(side="left", padx=(8, 0))
        Buton(arac, "Yeni", self.yeni_musteri, "birincil", genislik=76, ikon="+").pack(side="right")

        cerceve = tk.Frame(sol, bg=tema.PANEL, highlightbackground=tema.KENAR, highlightthickness=1)
        cerceve.pack(fill="both", expand=True)
        self.tablo = Tablo(cerceve, [
            ("kod", "Kod", 78, "w"),
            ("unvan", "Ünvan", 210, "w"),
            ("tip", "Tip", 82, "center"),
            ("sehir", "Şehir", 90, "w"),
            ("bakiye", "Bakiye", 100, "e"),
        ], yukseklik=18, secilince=self._secim_degisti, cift_tik=self.duzenle)
        self.tablo.pack(fill="both", expand=True, padx=1, pady=1)

        self.sayac = tk.Label(sol, text="", bg=tema.ZEMIN, fg=tema.YAZI_SOLUK,
                              font=tema.f("govde", 9), anchor="w")
        self.sayac.pack(fill="x", pady=(8, 0))

        # --- sag: detay
        self.sag = tk.Frame(kabuk, bg=tema.PANEL, highlightbackground=tema.KENAR,
                            highlightthickness=1)
        self.sag.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        self.bos = BosDurum(self.sag, "Detayları görmek için soldan bir müşteri seçin.", "◕")
        self.bos.pack(expand=True)
        self.detay = None

    def _ara(self, metin):
        self.arama_metni = metin
        self.yenile()

    def yenile(self):
        kayitlar = srv.musteriler(self.arama_metni, self.tip.al())
        satirlar = []
        for m in kayitlar:
            satirlar.append((m["id"], (
                m["kod"], m["unvan"], m["tip"], m["sehir"] or "-",
                para(m["bakiye"], False),
            )))
        self.tablo.doldur(satirlar, lambda k, d: "pasif" if not dict(
            (x["id"], x["aktif"]) for x in kayitlar).get(int(k), 1) else None)
        self.sayac.configure(text="{} müşteri · toplam açık bakiye {}".format(
            len(kayitlar), para(sum(m["bakiye"] for m in kayitlar if m["bakiye"] > 0))))
        if self.secili_id and self.tablo.agac.exists(str(self.secili_id)):
            self._detay_ciz(self.secili_id)
        elif self.detay is not None:
            self._detay_kapat()

    def _secim_degisti(self):
        kimlik = self.tablo.secili_kimlik()
        if kimlik:
            self.secili_id = int(kimlik)
            self._detay_ciz(self.secili_id)

    def _detay_kapat(self):
        if self.detay is not None:
            self.detay.destroy()
            self.detay = None
        self.secili_id = None
        self.bos.pack(expand=True)

    def _detay_ciz(self, musteri_id):
        m = srv.musteri(musteri_id)
        if m is None:
            self._detay_kapat()
            return
        self.bos.pack_forget()
        if self.detay is not None:
            self.detay.destroy()
        self.detay = MusteriDetay(self.sag, m, self)
        self.detay.pack(fill="both", expand=True)

    # --- islemler ---------------------------------------------------------

    def yeni_musteri(self):
        pencere = MusteriDialog(self, None)
        self.wait_window(pencere)
        if pencere.sonuc:
            self.secili_id = pencere.sonuc
            self.yenile()
            self.tablo.agac.selection_set(str(pencere.sonuc))
            self.bildir("Müşteri eklendi.")

    def duzenle(self, musteri_id=None):
        musteri_id = musteri_id or self.secili_id
        if not musteri_id:
            uyari_kutusu(self, "Seçim yok", "Düzenlemek için bir müşteri seçin.")
            return
        pencere = MusteriDialog(self, srv.musteri(musteri_id))
        self.wait_window(pencere)
        if pencere.sonuc:
            self.yenile()
            self.bildir("Müşteri güncellendi.")

    def sil(self, musteri_id):
        m = srv.musteri(musteri_id)
        ozet = srv.musteri_ozeti(musteri_id)
        mesaj = "'{}' kaydını silmek istediğinize emin misiniz?".format(m["unvan"])
        if ozet["adet"]:
            mesaj += "\n\n{} satış fişi bu müşteriye bağlı. Fişler silinmez, " \
                     "müşteri ünvanı fiş üzerinde kayıtlı kalır.".format(ozet["adet"])
        if not onay_kutusu(self, "Müşteriyi sil", mesaj):
            return
        srv.musteri_sil(musteri_id)
        self._detay_kapat()
        self.yenile()
        self.kabuk.sayfayi_tazele("panel")
        self.kabuk.rozetleri_yenile()
        self.bildir("Müşteri silindi.", "uyari")

    def gorusme_ekle(self, musteri_id, gorusme=None):
        pencere = GorusmeDialog(self, musteri_id, gorusme)
        self.wait_window(pencere)
        if pencere.sonuc:
            self._detay_ciz(musteri_id)
            self.kabuk.sayfayi_tazele("panel")
            self.kabuk.rozetleri_yenile()
            self.bildir("Görüşme kaydedildi.")


class MusteriDetay(tk.Frame):
    def __init__(self, ust, musteri, sayfa):
        super().__init__(ust, bg=tema.PANEL)
        self.musteri = musteri
        self.sayfa = sayfa
        ozet = srv.musteri_ozeti(musteri["id"])

        # baslik
        bas = tk.Frame(self, bg=tema.PANEL)
        bas.pack(fill="x", padx=18, pady=(16, 12))
        Avatar(bas, musteri["unvan"], boyut=46).pack(side="left")
        bilgi = tk.Frame(bas, bg=tema.PANEL)
        bilgi.pack(side="left", fill="x", expand=True, padx=(12, 0))
        tk.Label(bilgi, text=kisalt(musteri["unvan"], 34), bg=tema.PANEL, fg=tema.YAZI,
                 font=tema.f("baslik", 15, kalin=True), anchor="w").pack(fill="x")
        rozetler = tk.Frame(bilgi, bg=tema.PANEL)
        rozetler.pack(fill="x", pady=(4, 0))
        Rozet(rozetler, musteri["kod"], "gri").pack(side="left")
        Rozet(rozetler, musteri["tip"],
              "mor" if musteri["tip"] == "Kurumsal" else "mavi").pack(side="left", padx=5)
        if not musteri["aktif"]:
            Rozet(rozetler, "Pasif", "kirmizi").pack(side="left")

        dugmeler = tk.Frame(bas, bg=tema.PANEL)
        dugmeler.pack(side="right")
        Buton(dugmeler, "Düzenle", lambda: sayfa.duzenle(musteri["id"]), "ikincil",
              genislik=84, yukseklik=30).pack(side="left")
        Buton(dugmeler, "Sil", lambda: sayfa.sil(musteri["id"]), "sade",
              genislik=52, yukseklik=30).pack(side="left", padx=(6, 0))

        # ozet serit
        serit = tk.Frame(self, bg=tema.PANEL_ACIK)
        serit.pack(fill="x", padx=18)
        for i, (etiket, deger, renk) in enumerate([
            ("Toplam Ciro", para(ozet["ciro"]), tema.BASARI),
            ("Fiş Sayısı", sayi(ozet["adet"]), tema.YAZI),
            ("Ort. Sepet", para(ozet["ortalama"]), tema.YAZI),
            ("Bakiye", para(musteri["bakiye"]),
             tema.TEHLIKE if musteri["bakiye"] > 0 else tema.YAZI_SOLUK),
        ]):
            hucre = tk.Frame(serit, bg=tema.PANEL_ACIK)
            hucre.pack(side="left", fill="both", expand=True, pady=10)
            tk.Label(hucre, text=etiket.upper(), bg=tema.PANEL_ACIK, fg=tema.YAZI_PASIF,
                     font=tema.f("govde", 8, kalin=True)).pack()
            tk.Label(hucre, text=deger, bg=tema.PANEL_ACIK, fg=renk,
                     font=tema.f("mono", 11, kalin=True)).pack(pady=(3, 0))
            if i < 3:
                tk.Frame(serit, bg=tema.KENAR, width=1).pack(side="left", fill="y", pady=8)

        # sekmeler
        defter = ttk.Notebook(self, style="SF.TNotebook")
        defter.pack(fill="both", expand=True, padx=18, pady=(14, 16))
        defter.add(self._bilgi_sekmesi(defter), text="Bilgiler")
        defter.add(self._gorusme_sekmesi(defter), text="Görüşmeler ({})".format(ozet["gorusme"]))
        defter.add(self._satis_sekmesi(defter), text="Satın Almalar ({})".format(ozet["adet"]))

    def _bilgi_sekmesi(self, ust):
        m = self.musteri
        cer = tk.Frame(ust, bg=tema.PANEL)
        ic = tk.Frame(cer, bg=tema.PANEL)
        ic.pack(fill="both", expand=True, pady=14)
        alanlar = [
            ("Yetkili Kişi", m["yetkili"] or "-"),
            ("Telefon", m["telefon"] or "-"),
            ("E-posta", m["eposta"] or "-"),
            ("Şehir", m["sehir"] or "-"),
            ("Adres", m["adres"] or "-"),
            ("Vergi No", m["vergi_no"] or "-"),
            ("Kayıt Tarihi", tr_tarih(m["olusturma"])),
        ]
        for etiket, deger in alanlar:
            satir = tk.Frame(ic, bg=tema.PANEL)
            satir.pack(fill="x", pady=5)
            tk.Label(satir, text=etiket, bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9), width=15, anchor="w").pack(side="left")
            tk.Label(satir, text=deger, bg=tema.PANEL, fg=tema.YAZI,
                     font=tema.f("govde", 10), anchor="w", justify="left",
                     wraplength=340).pack(side="left", fill="x", expand=True)
        if m["notlar"]:
            tk.Frame(ic, bg=tema.KENAR, height=1).pack(fill="x", pady=10)
            tk.Label(ic, text="NOTLAR", bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 8, kalin=True), anchor="w").pack(fill="x")
            tk.Label(ic, text=m["notlar"], bg=tema.PANEL, fg=tema.YAZI_SOLUK,
                     font=tema.f("govde", 9), anchor="w", justify="left",
                     wraplength=420).pack(fill="x", pady=(4, 0))
        return cer

    def _gorusme_sekmesi(self, ust):
        cer = tk.Frame(ust, bg=tema.PANEL)
        arac = tk.Frame(cer, bg=tema.PANEL)
        arac.pack(fill="x", pady=(12, 8))
        tk.Label(arac, text="Müşteriyle yapılan tüm temaslar", bg=tema.PANEL,
                 fg=tema.YAZI_PASIF, font=tema.f("govde", 9)).pack(side="left")
        Buton(arac, "Görüşme Ekle", lambda: self.sayfa.gorusme_ekle(self.musteri["id"]),
              "birincil", genislik=118, yukseklik=30, ikon="+").pack(side="right")

        kayitlar = srv.gorusmeler(self.musteri["id"])
        if not kayitlar:
            BosDurum(cer, "Henüz görüşme kaydı yok.", "◌").pack(expand=True)
            return cer

        liste = tk.Frame(cer, bg=tema.PANEL)
        liste.pack(fill="both", expand=True)
        tuval = tk.Canvas(liste, bg=tema.PANEL, highlightthickness=0)
        kaydirici = ttk.Scrollbar(liste, orient="vertical", style="SF.Vertical.TScrollbar",
                                  command=tuval.yview)
        ic = tk.Frame(tuval, bg=tema.PANEL)
        ic.bind("<Configure>", lambda e: tuval.configure(scrollregion=tuval.bbox("all")))
        pencere = tuval.create_window((0, 0), window=ic, anchor="nw")
        tuval.bind("<Configure>", lambda e: tuval.itemconfigure(pencere, width=e.width))
        tuval.configure(yscrollcommand=kaydirici.set)
        tuval.pack(side="left", fill="both", expand=True)
        kaydirici.pack(side="right", fill="y")
        tuval.bind_all("<MouseWheel>", lambda e: tuval.yview_scroll(int(-e.delta / 120), "units"))

        renkler = {"Telefon": "mavi", "E-posta": "gri", "Ziyaret": "yesil",
                   "Toplantı": "mor", "Teklif": "vurgu", "Şikayet": "kirmizi"}
        for g in kayitlar:
            kutu = tk.Frame(ic, bg=tema.ZEBRA, highlightbackground=tema.KENAR, highlightthickness=1)
            kutu.pack(fill="x", pady=3, padx=(0, 4))
            govde = tk.Frame(kutu, bg=tema.ZEBRA)
            govde.pack(fill="x", padx=12, pady=10)
            bas = tk.Frame(govde, bg=tema.ZEBRA)
            bas.pack(fill="x")
            Rozet(bas, g["tip"], renkler.get(g["tip"], "gri")).pack(side="left")
            tk.Label(bas, text=g["konu"], bg=tema.ZEBRA, fg=tema.YAZI,
                     font=tema.f("govde", 10, kalin=True), anchor="w").pack(
                side="left", padx=8, fill="x", expand=True)
            tk.Label(bas, text=tr_tarih(g["tarih"]), bg=tema.ZEBRA, fg=tema.YAZI_PASIF,
                     font=tema.f("mono", 8)).pack(side="right")
            if g["notlar"]:
                tk.Label(govde, text=g["notlar"], bg=tema.ZEBRA, fg=tema.YAZI_SOLUK,
                         font=tema.f("govde", 9), anchor="w", justify="left",
                         wraplength=420).pack(fill="x", pady=(5, 0))
            ayak = tk.Frame(govde, bg=tema.ZEBRA)
            ayak.pack(fill="x", pady=(6, 0))
            if g["sonraki_takip"]:
                gecikti = g["sonraki_takip"] < bugun() and g["durum"] == "Açık"
                Rozet(ayak, "Takip: " + tr_tarih(g["sonraki_takip"]),
                      "kirmizi" if gecikti else "sari").pack(side="left")
            Rozet(ayak, g["durum"], "yesil" if g["durum"] == "Kapalı" else "gri").pack(
                side="left", padx=5)
            duzenle = tk.Label(ayak, text="düzenle", bg=tema.ZEBRA, fg=tema.YAZI_PASIF,
                               font=tema.f("govde", 8, kalin=True), cursor="hand2")
            duzenle.pack(side="right")
            duzenle.bind("<Button-1>", lambda e, k=g: self.sayfa.gorusme_ekle(
                self.musteri["id"], k))
            duzenle.bind("<Enter>", lambda e, w=duzenle: w.configure(fg=tema.VURGU_ACIK))
            duzenle.bind("<Leave>", lambda e, w=duzenle: w.configure(fg=tema.YAZI_PASIF))
        return cer

    def _satis_sekmesi(self, ust):
        cer = tk.Frame(ust, bg=tema.PANEL)
        kayitlar = srv.musteri_satislari(self.musteri["id"])
        if not kayitlar:
            BosDurum(cer, "Bu müşteriye ait satış yok.", "◌").pack(expand=True)
            return cer
        tablo = Tablo(cer, [
            ("fis", "Fiş No", 110, "w"),
            ("tarih", "Tarih", 90, "center"),
            ("odeme", "Ödeme", 100, "center"),
            ("toplam", "Tutar", 110, "e"),
        ], yukseklik=11)
        tablo.pack(fill="both", expand=True, pady=(12, 0))
        tablo.doldur([
            (s["id"], (s["fis_no"], tr_tarih(s["tarih"]), s["odeme_turu"], para(s["toplam"])))
            for s in kayitlar
        ], lambda k, d: "uyari" if d[2] == "Veresiye" else None)
        return cer


class MusteriDialog(TemelDialog):
    def __init__(self, ust, musteri):
        self.musteri = musteri
        super().__init__(ust, "Müşteri Kartı" if musteri else "Yeni Müşteri",
                         genislik=620, yukseklik=580,
                         alt_yazi=musteri["kod"] if musteri else "")

    def govde(self, ust):
        m = self.musteri
        izgara = tk.Frame(ust, bg=tema.ZEMIN)
        izgara.pack(fill="x")
        izgara.columnconfigure(0, weight=1, uniform="a")
        izgara.columnconfigure(1, weight=1, uniform="a")
        self.kod = Alan(izgara, "MÜŞTERİ KODU", m["kod"] if m else srv.musteri_kodu_uret(),
                        arka=tema.ZEMIN)
        self.kod.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.tip = Secim(izgara, "TİP", ["Bireysel", "Kurumsal"],
                         m["tip"] if m else "Bireysel", arka=tema.ZEMIN,
                         degisince=lambda v: self._tip_degisti())
        self.tip.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.unvan = Alan(ust, "ÜNVAN / AD SOYAD", m["unvan"] if m else "", arka=tema.ZEMIN)
        self.unvan.pack(fill="x", pady=(12, 0))

        izgara2 = tk.Frame(ust, bg=tema.ZEMIN)
        izgara2.pack(fill="x", pady=(12, 0))
        izgara2.columnconfigure(0, weight=1, uniform="b")
        izgara2.columnconfigure(1, weight=1, uniform="b")
        self.yetkili = Alan(izgara2, "YETKİLİ KİŞİ", m["yetkili"] if m else "", arka=tema.ZEMIN)
        self.yetkili.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.vergi = Alan(izgara2, "VERGİ NO", m["vergi_no"] if m else "", arka=tema.ZEMIN)
        self.vergi.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        izgara3 = tk.Frame(ust, bg=tema.ZEMIN)
        izgara3.pack(fill="x", pady=(12, 0))
        izgara3.columnconfigure(0, weight=1, uniform="c")
        izgara3.columnconfigure(1, weight=1, uniform="c")
        self.telefon = Alan(izgara3, "TELEFON", m["telefon"] if m else "", arka=tema.ZEMIN)
        self.telefon.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.eposta = Alan(izgara3, "E-POSTA", m["eposta"] if m else "", arka=tema.ZEMIN)
        self.eposta.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        izgara4 = tk.Frame(ust, bg=tema.ZEMIN)
        izgara4.pack(fill="x", pady=(12, 0))
        izgara4.columnconfigure(0, weight=1, uniform="d")
        izgara4.columnconfigure(1, weight=1, uniform="d")
        self.sehir = Secim(izgara4, "ŞEHİR", SEHIRLER, m["sehir"] if m else "Nevşehir",
                           arka=tema.ZEMIN, duzenlenebilir=True)
        self.sehir.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.bakiye = Alan(izgara4, "AÇILIŞ BAKİYESİ (₺)",
                           para(m["bakiye"], False) if m else "0,00", arka=tema.ZEMIN,
                           salt_okunur=bool(m),
                           ipucu="Satışlarla otomatik güncellenir" if m else "")
        self.bakiye.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.adres = CokSatir(ust, "ADRES", m["adres"] if m else "", satir=2, arka=tema.ZEMIN)
        self.adres.pack(fill="x", pady=(12, 0))
        self.notlar = CokSatir(ust, "NOTLAR", m["notlar"] if m else "", satir=3, arka=tema.ZEMIN)
        self.notlar.pack(fill="x", pady=(12, 0))

        self.aktif = tk.BooleanVar(value=bool(m["aktif"]) if m else True)
        tk.Checkbutton(ust, text=" Müşteri aktif", variable=self.aktif, bg=tema.ZEMIN,
                       fg=tema.YAZI_SOLUK, activebackground=tema.ZEMIN,
                       activeforeground=tema.VURGU_ACIK, selectcolor=tema.PANEL_ACIK,
                       bd=0, highlightthickness=0, font=tema.f("govde", 9),
                       cursor="hand2").pack(anchor="w", pady=(12, 0))
        self._tip_degisti()
        self.after(120, self.unvan.odak)

    def _tip_degisti(self):
        kurumsal = self.tip.al() == "Kurumsal"
        for alan in (self.yetkili, self.vergi):
            alan.giris.configure(state="normal" if kurumsal else "disabled")

    def kaydet(self):
        if not eposta_gecerli(self.eposta.al()):
            raise srv.IsKurali("E-posta adresi geçerli görünmüyor.")
        kimlik = srv.musteri_kaydet({
            "kod": self.kod.al(),
            "unvan": self.unvan.al(),
            "tip": self.tip.al(),
            "yetkili": self.yetkili.al(),
            "telefon": telefon_temizle(self.telefon.al()),
            "eposta": self.eposta.al(),
            "sehir": self.sehir.al(),
            "adres": self.adres.al(),
            "vergi_no": self.vergi.al(),
            "bakiye": ondalik(self.bakiye.al()),
            "notlar": self.notlar.al(),
            "aktif": self.aktif.get(),
        }, self.musteri["id"] if self.musteri else None)
        self.sonuc = kimlik
        return True


class GorusmeDialog(TemelDialog):
    def __init__(self, ust, musteri_id, gorusme=None):
        self.musteri_id = musteri_id
        self.gorusme = gorusme
        m = srv.musteri(musteri_id)
        super().__init__(ust, "Görüşme Kaydı", genislik=560, yukseklik=470,
                         alt_yazi=kisalt(m["unvan"], 28) if m else "")

    def govde(self, ust):
        g = self.gorusme
        izgara = tk.Frame(ust, bg=tema.ZEMIN)
        izgara.pack(fill="x")
        izgara.columnconfigure(0, weight=1, uniform="a")
        izgara.columnconfigure(1, weight=1, uniform="a")
        self.tip = Secim(izgara, "GÖRÜŞME TİPİ", srv.GORUSME_TIPLERI,
                         g["tip"] if g else "Telefon", arka=tema.ZEMIN)
        self.tip.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.tarih = TarihGirisi(izgara, "TARİH", g["tarih"] if g else bugun(), arka=tema.ZEMIN)
        self.tarih.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.konu = Alan(ust, "KONU", g["konu"] if g else "", arka=tema.ZEMIN)
        self.konu.pack(fill="x", pady=(12, 0))

        self.notlar = CokSatir(ust, "NOTLAR", g["notlar"] if g else "", satir=6, arka=tema.ZEMIN)
        self.notlar.pack(fill="both", expand=True, pady=(12, 0))

        izgara2 = tk.Frame(ust, bg=tema.ZEMIN)
        izgara2.pack(fill="x", pady=(12, 0))
        izgara2.columnconfigure(0, weight=1, uniform="b")
        izgara2.columnconfigure(1, weight=1, uniform="b")
        self.takip = TarihGirisi(izgara2, "SONRAKİ TAKİP", g["sonraki_takip"] if g else None,
                                 arka=tema.ZEMIN)
        self.takip.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.durum = Secim(izgara2, "DURUM", ["Açık", "Kapalı"], g["durum"] if g else "Açık",
                           arka=tema.ZEMIN)
        self.durum.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        tk.Label(ust, text="Takip tarihi girilen açık kayıtlar panelde ve menü rozetinde görünür.",
                 bg=tema.ZEMIN, fg=tema.YAZI_PASIF, font=tema.f("govde", 8),
                 anchor="w").pack(fill="x", pady=(8, 0))
        self.after(120, self.konu.odak)

    def dugmeleri_ekle(self):
        super().dugmeleri_ekle()
        if self.gorusme:
            Buton(self.dugmeler, "Sil", self._sil, "sade", genislik=58).pack(
                side="right", padx=(0, 8))

    def _sil(self):
        if onay_kutusu(self, "Görüşmeyi sil", "Bu görüşme kaydı silinsin mi?"):
            srv.gorusme_sil(self.gorusme["id"])
            self.sonuc = True
            self.destroy()

    def kaydet(self):
        srv.gorusme_kaydet({
            "musteri_id": self.musteri_id,
            "tarih": self.tarih.al() or bugun(),
            "tip": self.tip.al(),
            "konu": self.konu.al(),
            "notlar": self.notlar.al(),
            "sonraki_takip": self.takip.al(),
            "durum": self.durum.al(),
        }, self.gorusme["id"] if self.gorusme else None)
        self.sonuc = True
        return True
