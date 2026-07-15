@echo off
REM StockFlow - hata ayiklama baslaticisi
REM Uygulamayi konsol penceresi acik halde calistirir. Bir sorun cikarsa
REM hata mesaji bu pencerede kalir. Normal kullanim icin StockFlow.pyw
REM dosyasina cift tiklamak yeterli.
REM Anil Gul - 2025

cd /d "%~dp0"
title StockFlow

python --version >nul 2>&1
if errorlevel 1 goto pythonyok

echo StockFlow baslatiliyor...
echo.
python "StockFlow.pyw"
set cikis=%errorlevel%
echo.
if "%cikis%"=="0" (
    echo Uygulama kapandi.
) else (
    echo Uygulama hata ile kapandi. Cikis kodu: %cikis%
    echo Yukaridaki mesaji okuyun.
)
echo.
pause
exit /b %cikis%

:pythonyok
echo.
echo Python bulunamadi.
echo.
echo python.org/downloads adresinden kurun.
echo Kurulumda "Add python.exe to PATH" kutusunu isaretleyin,
echo bilesenler arasinda "tcl/tk and IDLE" secili kalsin.
echo.
pause
exit /b 1
