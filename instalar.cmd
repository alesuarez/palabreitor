@echo off
setlocal
chcp 65001 >nul
title Palabreitor - Instalacion de dependencias
cd /d "%~dp0"

echo ============================================
echo  Instalacion de Palabreitor
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] No se encontro Python.
        echo Instala Python 3.8+ desde https://www.python.org/downloads/
        echo Marca la casilla "Add python.exe to PATH" durante la instalacion.
        pause
        exit /b 1
    )
    set "PYCMD=py -3"
) else (
    set "PYCMD=python"
)

echo [1/4] Verificando entorno virtual...
if not exist ".venv\Scripts\python.exe" (
    echo       Creando .venv...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo       .venv ya existe.
)

echo [2/4] Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Fallo al actualizar pip.
    pause
    exit /b 1
)

echo [3/4] Instalando dependencias (faster-whisper + CUDA)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo al instalar las dependencias.
    pause
    exit /b 1
)

echo [4/4] Verificando ffmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [AVISO] ffmpeg no esta en el PATH.
    echo         Instalalo con:  winget install Gyan.FFmpeg -e
    echo         y reinicia la terminal.
) else (
    echo       ffmpeg encontrado.
)

echo.
echo ============================================
echo  Instalacion completada.
echo  Ahora abre una clase con doble clic en ejecutar.cmd
echo ============================================
pause