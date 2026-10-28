@echo off
setlocal
cd /d "%~dp0"
title Veeduria Ciudadana Cicuco Transparente - Servidor Python

echo ==========================================================
echo   VEEDURIA CIUDADANA CICUCO TRANSPARENTE (BOLIVAR)
echo   Plataforma Oficial en Python con Base de Datos SQLite
echo ==========================================================
echo.

:: Detectar comando de Python
set "PY_CMD=python"
python --version >nul 2>&1
if %errorlevel% equ 0 goto :found_python

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    goto :found_python
)

echo [ERROR] No se encontro Python en el sistema.
echo Por favor instala Python o verifica que este en tu PATH.
pause
exit /b 1

:found_python
echo [1/2] Verificando dependencias de Python...
"%PY_CMD%" -c "import flask, werkzeug, sqlite3" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando librerias necesarias desde requirements.txt...
    "%PY_CMD%" -m pip install -r requirements.txt
)

echo [2/2] Iniciando el servidor web y abriendo el navegador...
echo.
echo ----------------------------------------------------------
echo   Servidor activo en: http://127.0.0.1:5000/
echo.
echo   Panel de Administrador: Acceso discreto en pie de pagina
echo   o con atajo de teclado: Ctrl + Shift + A
echo   Contrasena de acceso: Veduria1969
echo.
echo   Para detener el servidor: presiona Ctrl + C en esta ventana.
echo ----------------------------------------------------------
echo.

"%PY_CMD%" app.py

pause
