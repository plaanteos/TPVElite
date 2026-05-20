@echo off
REM Script para construir el ejecutable de HeladeriaPOS
REM Autor: Jesus
REM Versión: 2.0.0

echo ========================================
echo Sistema TPV - Heladeria Profesional
echo Build Script v2.0.0
echo ========================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

echo [1/6] Verificando Python... OK
echo.

REM Verificar que el entorno virtual existe
if not exist "venv\" (
    echo [2/6] Creando entorno virtual...
    python -m venv venv
    echo Entorno virtual creado.
) else (
    echo [2/6] Entorno virtual encontrado... OK
)
echo.

REM Activar entorno virtual
echo [3/6] Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

REM Instalar/actualizar dependencias
echo [4/6] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
echo.

REM Limpiar builds anteriores
echo [5/6] Limpiando builds anteriores...
if exist "build\" rd /s /q build
if exist "dist\" rd /s /q dist
if exist "*.spec" del /q *.spec
echo Build anterior limpiado.
echo.

REM Construir ejecutable
echo [6/6] Construyendo ejecutable...
echo Esto puede tomar varios minutos...
echo.

pyinstaller --name=HeladeriaPOS ^
            --onefile ^
            --windowed ^
            --icon=icon.ico ^
            --add-data="config.json;." ^
            --hidden-import=PIL._tkinter_finder ^
            --hidden-import=matplotlib.backends.backend_tkagg ^
            --clean ^
            --noconfirm ^
            main.py

if errorlevel 1 (
    echo.
    echo ERROR: La construcción falló
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETADO EXITOSAMENTE
echo ========================================
echo.
echo El ejecutable se encuentra en: dist\HeladeriaPOS.exe
echo.
echo Para ejecutar la aplicación:
echo   cd dist
echo   HeladeriaPOS.exe
echo.
echo ========================================

REM Crear un archivo de versión
echo Version: 2.0.0 > dist\VERSION.txt
echo Build Date: %date% %time% >> dist\VERSION.txt
echo Build By: %username% >> dist\VERSION.txt

REM Copiar archivos necesarios
if exist "icon.ico" copy icon.ico dist\
if exist "config.json" copy config.json dist\
if exist "README.md" copy README.md dist\

echo.
echo Archivos adicionales copiados a dist\
echo.

pause
