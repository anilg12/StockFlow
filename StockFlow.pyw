# -*- coding: utf-8 -*-
# StockFlow · baslatici
#
# Windows'ta bu dosyaya cift tiklamak yeterli. .pyw uzantisi pythonw.exe ile
# eslesiyor, o yuzden arkada siyah konsol penceresi acilmiyor.
# Masaustune kisayol icin: sag tik > Gonder > Masaustu (kisayol olustur)
#
# Anıl Gül · 2025

import os
import sys

# Cift tiklamada calisma dizini bazen C:\Windows\System32 oluyor, o yuzden
# paketi bulabilmek icin dosyanin kendi klasorunu yola ekliyorum.
KOK = os.path.dirname(os.path.abspath(__file__))
if KOK not in sys.path:
    sys.path.insert(0, KOK)


def hata_goster(mesaj):
    """Konsol yoksa hatayi en azindan bir pencerede gosterelim."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        kok = tk.Tk()
        kok.withdraw()
        messagebox.showerror("StockFlow başlatılamadı", mesaj)
        kok.destroy()
    except Exception:
        sys.stderr.write(mesaj + "\n")


def main():
    if sys.version_info < (3, 8):
        hata_goster("StockFlow için Python 3.8 veya üzeri gerekiyor.\n"
                    "Kurulu sürüm: {}".format(sys.version.split()[0]))
        return 1
    try:
        import tkinter  # noqa: F401
    except ImportError:
        hata_goster("Python kurulumunuzda tkinter yok.\n\n"
                    "Windows: Python'u tekrar kurarken 'tcl/tk and IDLE' seçeneğini işaretleyin.\n"
                    "Linux: sudo apt install python3-tk")
        return 1

    try:
        from stockflow.uygulama import calistir
        return calistir()
    except Exception as hata:
        import traceback
        hata_goster("{}\n\n{}".format(hata, traceback.format_exc()))
        return 1


if __name__ == "__main__":
    sys.exit(main())
