@echo off
REM StockFlow - Windows baslatici (hata mesajlarini gormek isteyenler icin)
REM Anil Gul - 2025
cd /d "%~dp0"
start "" pythonw "StockFlow.pyw" 2>nul
if errorlevel 1 (
    echo pythonw bulunamadi, python ile deneniyor...
    python "StockFlow.pyw"
    pause
)
