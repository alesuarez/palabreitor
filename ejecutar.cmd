@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Palabreitor - Extraer guion de clase
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo [ERROR] No se encontro el entorno virtual.
    echo Ejecuta: py -m venv .venv
    echo y luego: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Arrastra el video de clase [mp4, mkv...] a esta ventana y presiona Enter.
    echo Tambien puedes escribirlo manualmente:
    set /p "VIDEO=Video: "
) else (
    set "VIDEO=%~1"
)

if not exist "%VIDEO%" (
    echo [ERROR] No existe el archivo: "%VIDEO%"
    pause
    exit /b 1
)

set "OUT=%~dpn1_script.txt"
if "%~1"=="" (
    set "OUT=%~dp0salida_script.txt"
)

echo.
echo Procesando: "%VIDEO%"
echo Salida:     "%OUT%"
echo.
"%PY%" palabreitor.py -i "%VIDEO%" -o "%OUT%"

echo.
if errorlevel 1 (
    echo [ERROR] Fallo el procesamiento.
) else (
    echo Listo. Revisa el archivo: "%OUT%"
)
echo.
pause