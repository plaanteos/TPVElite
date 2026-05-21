"""
Instalador - Sistema TPV Elite
Wizard de instalación paso a paso
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import shutil
import sys
import os
import winreg
import tempfile
import ctypes
import urllib.request

# ─── Instancia única (mutex de Windows) ──────────────────────────────────────
_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
_MUTEX_NAME = "Global\\TPVElite_Installer_Mutex"
_mutex_handle = _kernel32.CreateMutexW(None, True, _MUTEX_NAME)
if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
    ctypes.windll.user32.MessageBoxW(
        0,
        "El instalador ya está en ejecución.\nCerrá la ventana anterior antes de continuar.",
        "Sistema TPV Elite — Instalador",
        0x30
    )
    sys.exit(0)

# ─── Constantes ──────────────────────────────────────────────────────────────

APP_NAME    = "Sistema TPV Elite"
APP_VERSION = "2.0"
APP_AUTHOR  = "TPV Elite"
APP_FOLDER  = "TPVElite"          # sub-carpeta en destino
WIN_W, WIN_H = 720, 580

# Dependencias a instalar via pip
DEPS = [
    "bcrypt",
    "pillow",
    "reportlab",
    "openpyxl",
    "xlsxwriter",
    "python-dateutil",
    "libsql-client",
]

LICENSE_TEXT = """ACUERDO DE LICENCIA DE USO — Sistema TPV Elite

Copyright © 2024-2026 TPV Elite. Todos los derechos reservados.

1. CONCESIÓN DE LICENCIA
   Se le otorga una licencia limitada, no exclusiva e intransferible
   para instalar y usar este software en dispositivos de su propiedad
   o bajo su control, exclusivamente para fines comerciales legítimos.

2. RESTRICCIONES
   Queda estrictamente prohibido:
   a) Copiar, modificar o distribuir el software sin autorización.
   b) Realizar ingeniería inversa o descompilar el código fuente.
   c) Sub-licenciar o vender el software a terceros.
   d) Usar el software para actividades ilegales o no autorizadas.

3. PROPIEDAD INTELECTUAL
   El software, incluyendo su código fuente, diseño y documentación,
   es propiedad exclusiva de TPV Elite y está protegido por las leyes
   de propiedad intelectual aplicables.

4. GARANTÍA LIMITADA
   El software se proporciona "TAL CUAL". No se ofrecen garantías
   explícitas ni implícitas. El uso es bajo responsabilidad del usuario.

5. LIMITACIÓN DE RESPONSABILIDAD
   En ningún caso TPV Elite será responsable de daños directos,
   indirectos, incidentales o consecuentes derivados del uso o la
   imposibilidad de uso del software.

6. ACTUALIZACIONES
   Las actualizaciones del software pueden instalarse automáticamente
   y están sujetas a este mismo acuerdo o a uno actualizado.

7. TERMINACIÓN
   Esta licencia termina automáticamente si incumple cualquiera de sus
   términos. Al terminar, debe desinstalar y eliminar todas las copias.

8. LEY APLICABLE
   Este acuerdo se rige por las leyes vigentes en la jurisdicción del
   usuario final. Cualquier disputa se resolverá en los tribunales
   competentes de dicha jurisdicción.

Al hacer clic en "Acepto el acuerdo" y continuar con la instalación,
usted confirma haber leído, comprendido y aceptado todos los términos
de este acuerdo de licencia.
"""

# ─── Paleta de colores (installer claro moderno) ─────────────────────────────

C = {
    'bg':          '#F7F8FA',
    'sidebar':     '#1E2A3A',
    'sidebar_txt': '#FFFFFF',
    'sidebar_sub': '#8FA3B8',
    'card':        '#FFFFFF',
    'border':      '#E2E8F0',
    'accent':      '#5B5FEF',
    'accent_dark': '#4348D4',
    'text':        '#1A202C',
    'muted':       '#718096',
    'success':     '#38A169',
    'danger':      '#E53E3E',
    'warn':        '#D69E2E',
    'step_done':   '#38A169',
    'step_active': '#5B5FEF',
    'step_pend':   '#CBD5E0',
}

STEPS = [
    "Bienvenida",
    "Licencia",
    "Directorio",
    "Opciones",
    "Instalar",
    "Finalizado",
]

# ─── Utilidades ──────────────────────────────────────────────────────────────

def center_window(win, w, h):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x  = (sw - w) // 2
    y  = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def source_dir():
    """Raíz del proyecto — compatible con ejecución directa y con PyInstaller (.exe)"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS   # carpeta temporal de extracción del .exe
    return os.path.dirname(os.path.abspath(__file__))

def app_source():
    return os.path.join(source_dir(), "app")

def _is_real_python(path):
    """Verifica que el ejecutable sea Python real y no el stub del Microsoft Store.
    El stub de WindowsApps devuelve código de salida distinto de 0 cuando se le pasan args."""
    try:
        r = subprocess.run(
            [path, '-c', 'import sys; print(sys.version)'],
            capture_output=True, text=True, timeout=8
        )
        return r.returncode == 0 and r.stdout.strip() != ''
    except Exception:
        return False


def python_exe():
    """Devuelve pythonw.exe del sistema (Python real, no el stub de Microsoft Store).
    Cuando corre como exe PyInstaller, sys.executable es el propio installer."""
    if not getattr(sys, 'frozen', False):
        return sys.executable

    # 1. Python Launcher (py.exe) — lo más confiable en Windows
    py_launcher = shutil.which('py')
    if py_launcher and _is_real_python(py_launcher):
        try:
            r = subprocess.run(
                [py_launcher, '-c',
                 'import sys,os; pw=os.path.join(os.path.dirname(sys.executable),"pythonw.exe"); '
                 'print(pw if os.path.exists(pw) else sys.executable)'],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass

    # 2. Buscar en PATH — excluir el stub de Microsoft Store (WindowsApps)
    for name in ('pythonw.exe', 'python.exe'):
        found = shutil.which(name)
        if found and 'WindowsApps' not in found and _is_real_python(found):
            return found

    # 3. Buscar en el Registro de Windows
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for subkey in (
            r'SOFTWARE\Python\PythonCore',
            r'SOFTWARE\WOW6432Node\Python\PythonCore',
        ):
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    i = 0
                    while True:
                        try:
                            ver = winreg.EnumKey(k, i)
                            with winreg.OpenKey(hive, f'{subkey}\\{ver}\\InstallPath') as kp:
                                path = winreg.QueryValue(kp, '').strip()
                                for name in ('pythonw.exe', 'python.exe'):
                                    full = os.path.join(path, name)
                                    if os.path.exists(full) and _is_real_python(full):
                                        return full
                            i += 1
                        except OSError:
                            break
            except OSError:
                continue

    raise RuntimeError(
        "No se encontró Python instalado en el sistema.\n"
        "Instalá Python desde https://python.org y volvé a ejecutar el instalador."
    )

# ─── Instalador ──────────────────────────────────────────────────────────────

class Installer:
    """Lógica de instalación separada de la UI"""

    def __init__(self, dest_dir, opts):
        self.dest_dir  = dest_dir          # directorio final de instalación
        self.opts      = opts              # dict de opciones
        self.app_dest  = dest_dir          # se instala directo en la carpeta elegida
        self.log_lines = []
        self.on_step   = None             # callback(msg)
        self.on_prog   = None             # callback(pct 0-100)

    def _emit(self, msg, pct=None):
        self.log_lines.append(msg)
        if self.on_step:
            self.on_step(msg)
        if pct is not None and self.on_prog:
            self.on_prog(pct)

    def run(self):
        try:
            self._copy_files()
            self._install_deps()
            self._create_launcher()
            if self.opts.get('shortcut_desktop'):
                self._create_shortcut_desktop()
            if self.opts.get('shortcut_menu'):
                self._create_shortcut_menu()
            self._emit("✅ Instalación completada con éxito.", 100)
            return True, None
        except Exception as exc:
            self._emit(f"❌ Error: {exc}", None)
            return False, str(exc)

    def _copy_files(self):
        self._emit("📂 Copiando archivos de la aplicación…", 5)
        src = app_source()
        dst = self.app_dest

        # Detectar si el app está corriendo (tiene archivos bloqueados)
        if os.path.exists(dst):
            main_py = os.path.join(dst, "main.py")
            db_file = os.path.join(dst, "database.db")
            # Intentar abrir en escritura para detectar si están bloqueados
            for check_file in (db_file, main_py):
                if os.path.exists(check_file):
                    try:
                        with open(check_file, 'a'):
                            pass
                    except PermissionError:
                        raise RuntimeError(
                            "El Sistema TPV Elite está abierto.\n"
                            "Cerrá la aplicación antes de continuar con la instalación."
                        )

        # Instalación limpia: eliminar .db y config antes de copiar
        if self.opts.get('reset_data'):
            self._emit("   🗑  Limpiando datos anteriores…")
            for pattern in ('*.db', '*.db-shm', '*.db-wal', 'config.json', 'logs'):
                import glob
                for f in glob.glob(os.path.join(dst, pattern)):
                    try:
                        if os.path.isfile(f):
                            os.remove(f)
                        elif os.path.isdir(f):
                            shutil.rmtree(f)
                    except OSError:
                        pass

        # Crear destino si no existe; si existe, copiar encima sin borrar.
        # Se excluyen archivos .db para no sobreescribir la base de datos del usuario.
        os.makedirs(dst, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.db', '*.db-shm', '*.db-wal'))
        self._emit(f"   → Archivos copiados a: {dst}", 30)

    def _install_deps(self):
        self._emit("📦 Instalando dependencias de Python…", 35)
        py = python_exe()
        for i, dep in enumerate(DEPS, 1):
            self._emit(f"   → Instalando {dep}…")
            result = subprocess.run(
                [py, "-m", "pip", "install", dep, "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                self._emit(f"   ⚠ Advertencia con {dep}: {result.stderr[:80]}")
            pct = 35 + int((i / len(DEPS)) * 35)
            self._emit(f"   ✓ {dep}", pct)
        self._emit("   ✓ Dependencias listas.", 70)

    def _create_launcher(self):
        self._emit("🚀 Creando lanzador…", 75)
        py = python_exe()  # Ruta completa al Python del sistema destino
        # Preferir pythonw.exe (sin consola) si existe junto a python.exe
        pythonw = os.path.join(os.path.dirname(py), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = py
        main = os.path.join(self.app_dest, "main.py")

        # Lanzador principal: .vbs con la ruta COMPLETA al pythonw del sistema.
        # No usar "pythonw" por nombre porque puede no estar en PATH.
        vbs = os.path.join(self.app_dest, "Lanzar TPV Elite.vbs")
        with open(vbs, "w", encoding="utf-8") as f:
            f.write(
                'Set WS = CreateObject("WScript.Shell")\n'
                f'WS.CurrentDirectory = "{self.app_dest}"\n'
                f'WS.Run Chr(34) & "{pythonw}" & Chr(34)'
                f' & " " & Chr(34) & "{main}" & Chr(34), 0\n'
                'Set WS = Nothing\n'
            )
        self._emit(f"   → Lanzador: {vbs}", 78)

        # Lanzador de debug: .bat con ruta completa a python.exe y
        # pausa automática en caso de error.
        bat = os.path.join(self.app_dest, "Debug - Abrir con consola.bat")
        with open(bat, "w", encoding="utf-8") as f:
            f.write(
                f'@echo off\n'
                f'cd /d "{self.app_dest}"\n'
                f'echo Iniciando {APP_NAME}...\n'
                f'"{py}" "{main}"\n'
                f'if %ERRORLEVEL% NEQ 0 (\n'
                f'    echo.\n'
                f'    echo La aplicacion cerro con error %ERRORLEVEL%\n'
                f'    echo Revisa los logs en: {self.app_dest}\\logs\n'
                f'    pause\n'
                f')\n'
            )
        self._emit(f"   → Debug: {bat}", 80)

    def _ps_shortcut(self, lnk_path):
        """Crea un acceso directo .lnk via PowerShell usando archivo .ps1 temporal
        para evitar problemas de escaping en rutas con espacios o caracteres especiales."""
        vbs  = os.path.join(self.app_dest, "Lanzar TPV Elite.vbs")
        icon = os.path.join(self.app_dest, "tpvelite.ico")

        # El shortcut apunta a wscript.exe + el .vbs lanzador.
        # Esto evita que aparezca una ventana CMD al hacer doble clic,
        # y es equivalente a la configuración anterior con pythonw.exe.
        wscript = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"),
                               "System32", "wscript.exe")

        # Escribir script .ps1 a archivo temporal — sin problemas de escape
        ps_content = (
            f"$s = New-Object -COM WScript.Shell\n"
            f"$lnk = $s.CreateShortcut('{lnk_path}')\n"
            f"$lnk.TargetPath = '{wscript}'\n"
            f"$lnk.Arguments = '\"{vbs}\"'\n"
            f"$lnk.WorkingDirectory = '{self.app_dest}'\n"
            f"$lnk.Description = '{APP_NAME}'\n"
            f"$lnk.IconLocation = '{icon},0'\n"
            f"$lnk.Save()\n"
        )
        ps_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1',
                                             delete=False, encoding='utf-8') as f:
                f.write(ps_content)
                ps_file = f.name

            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                self._emit(f"   ⚠ Acceso directo: {result.stderr[:120]}")
        finally:
            if ps_file and os.path.exists(ps_file):
                os.unlink(ps_file)

    def _refresh_search_index(self):
        """Fuerza a Windows a reindexar el menú inicio para que la app aparezca en búsqueda."""
        try:
            subprocess.run(["ie4uinit.exe", "-show"], capture_output=True)
        except Exception:
            pass

    def _create_shortcut_desktop(self):
        self._emit("🖥  Creando acceso directo en el escritorio…", 85)
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        # Intentar también con la ruta localizada del escritorio
        if not os.path.isdir(desktop):
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetFolderPathW(0, 0x0000, 0, 0, buf)
            desktop = buf.value
        lnk = os.path.join(desktop, f"{APP_NAME}.lnk")
        self._ps_shortcut(lnk)
        self._emit(f"   → {lnk}", 88)

    def _create_shortcut_menu(self):
        self._emit("📌 Creando acceso en el menú Inicio…", 90)
        # Directamente en Programs (sin subcarpeta) para que Windows lo indexe bien
        menu_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs"
        )
        os.makedirs(menu_dir, exist_ok=True)
        lnk = os.path.join(menu_dir, f"{APP_NAME}.lnk")
        self._ps_shortcut(lnk)
        self._emit(f"   → {lnk}", 93)
        self._register_app()

    def _register_app(self):
        """Registra la app en el Registry para que aparezca en búsqueda de Windows"""
        self._emit("📋 Registrando en Windows…", 95)
        key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_FOLDER}"
        py = python_exe()
        pythonw = os.path.join(os.path.dirname(py), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = py
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                winreg.SetValueEx(k, "DisplayName",     0, winreg.REG_SZ,    APP_NAME)
                winreg.SetValueEx(k, "DisplayVersion",  0, winreg.REG_SZ,    APP_VERSION)
                winreg.SetValueEx(k, "Publisher",       0, winreg.REG_SZ,    APP_AUTHOR)
                winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ,    self.app_dest)
                winreg.SetValueEx(k, "DisplayIcon",     0, winreg.REG_SZ,    pythonw)
                winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                                  f'cmd /c rmdir /s /q "{self.app_dest}"')
                winreg.SetValueEx(k, "NoModify",        0, winreg.REG_DWORD,  1)
                winreg.SetValueEx(k, "NoRepair",        0, winreg.REG_DWORD,  1)
            self._emit("   ✓ App registrada en Windows.", 97)
        except Exception as e:
            self._emit(f"   ⚠ No se pudo registrar: {e}")
        self._refresh_search_index()


# ─── Wizard UI ───────────────────────────────────────────────────────────────

class SetupWizard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"Instalación — {APP_NAME} {APP_VERSION}")
        self.resizable(False, False)
        self.configure(bg=C['bg'])
        center_window(self, WIN_W, WIN_H)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Estado
        self.current_step = 0
        self.license_accepted = tk.BooleanVar(value=False)
        self.install_dir = tk.StringVar(
            value=os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), APP_FOLDER)
        )
        self.opt_desktop    = tk.BooleanVar(value=True)
        self.opt_menu       = tk.BooleanVar(value=True)
        self.opt_launch     = tk.BooleanVar(value=True)
        self.opt_reset_data = tk.BooleanVar(value=False)

        self._build_layout()
        self._show_step(0)

    # ── Layout principal ─────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar izquierdo
        self.sidebar = tk.Frame(self, bg=C['sidebar'], width=200)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # Área de contenido derecha
        right = tk.Frame(self, bg=C['bg'])
        right.pack(side='left', fill='both', expand=True)

        # Contenido scrollable
        self.content = tk.Frame(right, bg=C['bg'])
        self.content.pack(fill='both', expand=True, padx=32, pady=16)

        # Separador + botones de navegación
        sep = tk.Frame(right, bg=C['border'], height=1)
        sep.pack(fill='x', padx=0)

        nav = tk.Frame(right, bg=C['bg'])
        nav.pack(fill='x', padx=28, pady=14)

        self.btn_back = tk.Button(
            nav, text="◀  Anterior", font=('Segoe UI', 10),
            bg=C['card'], fg=C['text'], bd=1, relief='flat',
            padx=18, pady=8, cursor='hand2',
            command=self._prev
        )
        self.btn_back.pack(side='left')

        self.btn_next = tk.Button(
            nav, text="Siguiente  ▶", font=('Segoe UI', 10, 'bold'),
            bg=C['accent'], fg='white', bd=0, relief='flat',
            padx=22, pady=8, cursor='hand2',
            command=self._next
        )
        self.btn_next.pack(side='right')

        self.btn_cancel = tk.Button(
            nav, text="Cancelar", font=('Segoe UI', 10),
            bg=C['bg'], fg=C['muted'], bd=0, relief='flat',
            padx=14, pady=8, cursor='hand2',
            command=self._on_close
        )
        self.btn_cancel.pack(side='right', padx=(0, 8))

    def _build_sidebar(self):
        # Logo / título
        header = tk.Frame(self.sidebar, bg=C['accent'], height=90)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="🏪", font=('Segoe UI', 32),
                 bg=C['accent'], fg='white').place(relx=.5, rely=.45, anchor='center')

        tk.Label(self.sidebar, text=APP_NAME,
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['sidebar'], fg=C['sidebar_txt'],
                 wraplength=170, justify='center').pack(pady=(16, 2))
        tk.Label(self.sidebar, text=f"Versión {APP_VERSION}",
                 font=('Segoe UI', 8),
                 bg=C['sidebar'], fg=C['sidebar_sub']).pack(pady=(0, 24))

        # Separador
        tk.Frame(self.sidebar, bg='#2D3E50', height=1).pack(fill='x', padx=16, pady=(0, 16))

        # Lista de pasos
        self.step_frames = []
        for i, name in enumerate(STEPS):
            frm = tk.Frame(self.sidebar, bg=C['sidebar'])
            frm.pack(fill='x', padx=16, pady=3)

            circle = tk.Label(frm, text=str(i + 1), width=2,
                              font=('Segoe UI', 8, 'bold'),
                              bg=C['step_pend'], fg='white',
                              relief='flat')
            circle.pack(side='left')

            lbl = tk.Label(frm, text=name,
                           font=('Segoe UI', 9),
                           bg=C['sidebar'], fg=C['sidebar_sub'],
                           anchor='w')
            lbl.pack(side='left', padx=(8, 0))

            self.step_frames.append((frm, circle, lbl))

    def _update_sidebar(self, active):
        for i, (frm, circle, lbl) in enumerate(self.step_frames):
            if i < active:
                circle.configure(bg=C['step_done'], text="✓")
                lbl.configure(fg=C['sidebar_sub'])
            elif i == active:
                circle.configure(bg=C['step_active'], text=str(i + 1))
                lbl.configure(fg='white', font=('Segoe UI', 9, 'bold'))
            else:
                circle.configure(bg=C['step_pend'], text=str(i + 1))
                lbl.configure(fg=C['sidebar_sub'], font=('Segoe UI', 9))

    # ── Navegación ───────────────────────────────────────────────────────────

    def _show_step(self, idx):
        for w in self.content.winfo_children():
            w.destroy()
        self.current_step = idx
        self._update_sidebar(idx)

        [
            self._page_welcome,
            self._page_license,
            self._page_directory,
            self._page_options,
            self._page_install,
            self._page_done,
        ][idx]()

        # Ajustar botones según paso
        self.btn_back.configure(state='normal' if idx > 0 else 'disabled')
        is_last = idx == len(STEPS) - 1
        is_inst = idx == 4
        if is_last:
            # Botones manejados dentro de _page_done
            self.btn_next.pack_forget()
            self.btn_back.pack_forget()
            self.btn_cancel.pack_forget()
        elif is_inst:
            self.btn_next.pack_forget()
            self.btn_back.pack_forget()
            self.btn_cancel.pack_forget()
        else:
            self.btn_next.configure(text="Siguiente  ▶", command=self._next)
            self.btn_next.pack(side='right')
            self.btn_back.pack(side='left')
            self.btn_cancel.pack(side='right', padx=(0, 8))

    def _next(self):
        # Validaciones por paso
        if self.current_step == 0:
            if not self._check_or_install_python():
                return
        if self.current_step == 1 and not self.license_accepted.get():
            messagebox.showwarning(
                "Licencia",
                "Debes aceptar el acuerdo de licencia para continuar.",
                parent=self
            )
            return
        if self.current_step < len(STEPS) - 1:
            self._show_step(self.current_step + 1)

    def _check_or_install_python(self):
        """Verifica si Python está disponible. Si no, lo descarga e instala automáticamente.
        Devuelve True si Python quedó disponible, False si el usuario canceló o falló."""
        try:
            python_exe()
            return True
        except RuntimeError:
            pass

        respuesta = messagebox.askyesno(
            "Python no encontrado",
            "Esta aplicación requiere Python 3.x para funcionar.\n\n"
            "Python no está instalado en este equipo.\n\n"
            "¿Querés que lo instalemos automáticamente? (~25 MB)\n"
            "Se instalará Python 3.13 en silencio mientras seguís con el asistente.",
            parent=self
        )
        if not respuesta:
            import webbrowser
            webbrowser.open("https://www.python.org/downloads/")
            return False

        return self._instalar_python_auto()

    def _instalar_python_auto(self):
        """Descarga e instala Python 3.13 silenciosamente.
        Muestra ventana de progreso. Devuelve True si quedó disponible."""
        PYTHON_URL = "https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe"

        # --- Ventana de progreso ---
        dlg = tk.Toplevel(self)
        dlg.title("Instalando Python…")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=C['bg'])
        center_window(dlg, 440, 170)

        tk.Label(dlg, text="⏳  Instalando Python 3.13 automáticamente…",
                 font=('Segoe UI', 11, 'bold'),
                 bg=C['bg'], fg=C['text']).pack(pady=(22, 6))

        status_var = tk.StringVar(value="Descargando Python (~25 MB)…")
        tk.Label(dlg, textvariable=status_var,
                 font=('Segoe UI', 9), bg=C['bg'], fg=C['muted']).pack()

        prog = ttk.Progressbar(dlg, mode='indeterminate', length=380)
        prog.pack(pady=(12, 22))
        prog.start(10)

        resultado = {'ok': False, 'error': None}

        def _hilo():
            tmp_exe = None
            try:
                # 1. Descargar
                tmp_exe = tempfile.mktemp(suffix='.exe')
                urllib.request.urlretrieve(PYTHON_URL, tmp_exe)

                # 2. Instalar silenciosamente para el usuario actual, agrega al PATH
                dlg.after(0, lambda: status_var.set("Instalando Python (puede tardar un momento)…"))
                subprocess.run(
                    [
                        tmp_exe,
                        '/quiet',
                        'InstallAllUsers=0',
                        'PrependPath=1',
                        'Include_launcher=1',
                        'Include_test=0',
                        'Include_doc=0',
                    ],
                    check=True, timeout=300
                )
                resultado['ok'] = True
            except Exception as exc:
                resultado['error'] = str(exc)
            finally:
                if tmp_exe and os.path.exists(tmp_exe):
                    try:
                        os.unlink(tmp_exe)
                    except OSError:
                        pass
                dlg.after(0, dlg.destroy)

        threading.Thread(target=_hilo, daemon=True).start()
        self.wait_window(dlg)

        if not resultado['ok']:
            messagebox.showerror(
                "Error al instalar Python",
                f"No se pudo instalar Python automáticamente.\n\n"
                f"Error: {resultado['error']}\n\n"
                "Instalalo manualmente desde python.org y volvé a ejecutar el instalador.",
                parent=self
            )
            import webbrowser
            webbrowser.open("https://www.python.org/downloads/")
            return False

        # 3. Recargar PATH desde el registro para que python_exe() lo encuentre
        #    (el proceso actual no recibe el cambio de PATH del instalador)
        for hive, subkey in [
            (winreg.HKEY_CURRENT_USER, 'Environment'),
            (winreg.HKEY_LOCAL_MACHINE,
             r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
        ]:
            try:
                with winreg.OpenKey(hive, subkey) as k:
                    val, _ = winreg.QueryValueEx(k, 'PATH')
                    if val and val not in os.environ.get('PATH', ''):
                        os.environ['PATH'] = os.environ.get('PATH', '') + ';' + val
            except OSError:
                pass

        # 4. Verificar que ahora se detecte
        try:
            python_exe()
            messagebox.showinfo(
                "Python instalado",
                "✅ Python 3.13 se instaló correctamente.\n"
                "La instalación del Sistema TPV Elite continuará ahora.",
                parent=self
            )
            return True
        except RuntimeError:
            messagebox.showerror(
                "Python instalado pero no detectado",
                "Python se instaló pero no pudo ser detectado en esta sesión.\n\n"
                "Cerrá y volvé a ejecutar el instalador para que tome efecto.",
                parent=self
            )
            return False

    def _prev(self):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _on_close(self):
        if self.current_step == 4:
            return   # No cerrar mientras instala
        if messagebox.askyesno("Cancelar instalación",
                               "¿Seguro que querés cancelar la instalación?",
                               parent=self):
            self.destroy()

    # ── Helpers de UI ────────────────────────────────────────────────────────

    def _page_title(self, icon, title, subtitle=None):
        hdr = tk.Frame(self.content, bg=C['bg'])
        hdr.pack(fill='x', pady=(0, 20))
        tk.Label(hdr, text=icon, font=('Segoe UI', 28),
                 bg=C['bg']).pack(side='left', padx=(0, 14))
        txt = tk.Frame(hdr, bg=C['bg'])
        txt.pack(side='left', fill='y', anchor='w')
        tk.Label(txt, text=title, font=('Segoe UI', 16, 'bold'),
                 bg=C['bg'], fg=C['text']).pack(anchor='w')
        if subtitle:
            tk.Label(txt, text=subtitle, font=('Segoe UI', 10),
                     bg=C['bg'], fg=C['muted']).pack(anchor='w')
        tk.Frame(self.content, bg=C['border'], height=1).pack(fill='x', pady=(0, 18))

    def _card(self, parent=None):
        p = parent or self.content
        f = tk.Frame(p, bg=C['card'],
                     highlightbackground=C['border'],
                     highlightthickness=1)
        f.pack(fill='x', pady=(0, 12))
        return f

    # ── Páginas ──────────────────────────────────────────────────────────────

    def _page_welcome(self):
        # Centrado vertical (usa place)
        box = tk.Frame(self.content, bg=C['bg'])
        box.place(relx=.5, rely=.45, anchor='center')

        tk.Label(box, text="🏪", font=('Segoe UI', 54),
                 bg=C['bg']).pack()
        tk.Label(box, text=APP_NAME,
                 font=('Segoe UI', 20, 'bold'),
                 bg=C['bg'], fg=C['text']).pack(pady=(10, 4))
        tk.Label(box, text=f"Versión {APP_VERSION}  —  Sistema de Punto de Venta Elite",
                 font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['muted']).pack()

        tk.Frame(box, bg=C['accent'], height=3, width=80).pack(pady=18)

        desc = (
            "Este asistente te guiará por cada paso de la instalación.\n\n"
            "• Se copiarán los archivos de la aplicación.\n"
            "• Se instalarán las dependencias necesarias.\n"
            "• Se crearán los accesos directos que elijas.\n\n"
            "Hacé clic en Siguiente para comenzar."
        )
        tk.Label(box, text=desc,
                 font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['text'],
                 justify='left', wraplength=400).pack()

    def _page_license(self):
        self._page_title("📄", "Acuerdo de Licencia",
                         "Leé el acuerdo antes de continuar.")

        # Área de texto con altura fija para que los radios siempre queden visibles
        txt_frame = tk.Frame(self.content, bg=C['border'],
                             highlightbackground=C['border'], highlightthickness=1)
        txt_frame.pack(fill='x')

        sb = tk.Scrollbar(txt_frame)
        sb.pack(side='right', fill='y')

        txt = tk.Text(txt_frame, font=('Segoe UI', 9),
                      bg=C['card'], fg=C['text'],
                      relief='flat', padx=12, pady=10,
                      wrap='word', height=14,
                      yscrollcommand=sb.set,
                      state='normal')
        txt.insert('end', LICENSE_TEXT)
        txt.configure(state='disabled')
        txt.pack(side='left', fill='x', expand=True)
        sb.configure(command=txt.yview)

        # Separador
        tk.Frame(self.content, bg=C['border'], height=1).pack(fill='x', pady=(14, 8))

        # Radios — siempre visibles debajo del área de texto
        radio_frame = tk.Frame(self.content, bg=C['bg'])
        radio_frame.pack(fill='x')

        tk.Radiobutton(radio_frame,
                       text="  Acepto el acuerdo",
                       variable=self.license_accepted, value=True,
                       font=('Segoe UI', 10, 'bold'),
                       bg=C['bg'], fg=C['text'],
                       activebackground=C['bg'],
                       selectcolor=C['accent']).pack(anchor='w')

        tk.Radiobutton(radio_frame,
                       text="  No acepto el acuerdo",
                       variable=self.license_accepted, value=False,
                       font=('Segoe UI', 10),
                       bg=C['bg'], fg=C['muted'],
                       activebackground=C['bg'],
                       selectcolor=C['accent']).pack(anchor='w', pady=(4, 0))

    def _page_directory(self):
        self._page_title("📁", "Directorio de instalación",
                         "Elegí dónde instalar la aplicación.")

        card = self._card()
        inner = tk.Frame(card, bg=C['card'])
        inner.pack(fill='x', padx=16, pady=14)

        tk.Label(inner, text="Instalar en:",
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['text']).pack(anchor='w')

        row = tk.Frame(inner, bg=C['card'])
        row.pack(fill='x', pady=(6, 0))

        entry = tk.Entry(row, textvariable=self.install_dir,
                         font=('Segoe UI', 10),
                         bg=C['bg'], fg=C['text'],
                         relief='flat',
                         highlightbackground=C['border'],
                         highlightthickness=1)
        entry.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))

        def browse():
            d = filedialog.askdirectory(parent=self, title="Seleccionar carpeta")
            if d:
                self.install_dir.set(os.path.join(d, APP_FOLDER))

        tk.Button(row, text="Examinar…",
                  font=('Segoe UI', 10),
                  bg=C['accent'], fg='white', bd=0, relief='flat',
                  padx=14, pady=6, cursor='hand2',
                  command=browse).pack(side='left')

        tk.Label(inner, text=(
            "Si la carpeta no existe, se creará automáticamente.\n"
            f"Se necesitan aproximadamente 50 MB de espacio libre."
        ),
                 font=('Segoe UI', 9),
                 bg=C['card'], fg=C['muted'],
                 justify='left').pack(anchor='w', pady=(10, 0))

        # Ruta final preview
        preview_card = self._card()
        prev_inner = tk.Frame(preview_card, bg=C['card'])
        prev_inner.pack(fill='x', padx=16, pady=12)
        tk.Label(prev_inner, text="La aplicación se instalará en:",
                 font=('Segoe UI', 9),
                 bg=C['card'], fg=C['muted']).pack(anchor='w')
        self._dir_preview = tk.Label(prev_inner, text=self.install_dir.get(),
                                     font=('Segoe UI', 9, 'bold'),
                                     bg=C['card'], fg=C['accent'],
                                     wraplength=380, justify='left')
        self._dir_preview.pack(anchor='w')
        self.install_dir.trace_add('write', lambda *_: self._dir_preview.configure(
            text=self.install_dir.get()))

    def _page_options(self):
        self._page_title("⚙", "Opciones de instalación",
                         "Configurá los accesos y preferencias.")

        card = self._card()
        inner = tk.Frame(card, bg=C['card'])
        inner.pack(fill='x', padx=16, pady=14)

        tk.Label(inner, text="Accesos directos",
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['text']).pack(anchor='w', pady=(0, 8))

        for var, text, sub in [
            (self.opt_desktop, "Crear acceso directo en el Escritorio",
             "Se añadirá un ícono en tu escritorio para abrir la app."),
            (self.opt_menu,    "Agregar al Menú Inicio",
             "Se creará una entrada en Programas > TPVElite."),
            (self.opt_launch,  "Abrir la aplicación al terminar",
             "Se iniciará el sistema TPV al finalizar la instalación."),
        ]:
            row = tk.Frame(inner, bg=C['card'])
            row.pack(fill='x', pady=(0, 5))
            chk = tk.Checkbutton(row, variable=var,
                                 bg=C['card'], activebackground=C['card'],
                                 selectcolor=C['accent'])
            chk.pack(side='left')
            txt_col = tk.Frame(row, bg=C['card'])
            txt_col.pack(side='left', padx=(4, 0))
            tk.Label(txt_col, text=text,
                     font=('Segoe UI', 10, 'bold'),
                     bg=C['card'], fg=C['text']).pack(anchor='w')
            tk.Label(txt_col, text=sub,
                     font=('Segoe UI', 8),
                     bg=C['card'], fg=C['muted']).pack(anchor='w')

        # Opción inicio limpio
        sep = tk.Frame(inner, bg=C['border'], height=1)
        sep.pack(fill='x', pady=(10, 8))
        tk.Label(inner, text="Datos",
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['text']).pack(anchor='w', pady=(0, 6))
        reset_row = tk.Frame(inner, bg=C['card'])
        reset_row.pack(fill='x')
        chk_reset = tk.Checkbutton(reset_row, variable=self.opt_reset_data,
                                   bg=C['card'], activebackground=C['card'],
                                   selectcolor=C['danger'])
        chk_reset.pack(side='left')
        txt_reset = tk.Frame(reset_row, bg=C['card'])
        txt_reset.pack(side='left', padx=(4, 0))
        tk.Label(txt_reset, text="⚠️  Instalación limpia (nuevo cliente)",
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['warn']).pack(anchor='w')
        tk.Label(txt_reset, text="Elimina la base de datos y configuración existentes. Usar solo en equipos nuevos.",
                 font=('Segoe UI', 8),
                 bg=C['card'], fg=C['muted']).pack(anchor='w')

        # Resumen
        sum_card = self._card()
        sum_inner = tk.Frame(sum_card, bg=C['card'])
        sum_inner.pack(fill='x', padx=16, pady=8)
        tk.Label(sum_inner, text="Resumen de instalación",
                 font=('Segoe UI', 10, 'bold'),
                 bg=C['card'], fg=C['text']).pack(anchor='w', pady=(0, 6))
        for line in [
            f"📁  Destino:  {self.install_dir.get()}",
            f"🐍  Python:   {sys.version.split()[0]}",
            f"📦  Deps:     {', '.join(DEPS[:3])}…",
        ]:
            tk.Label(sum_inner, text=line,
                     font=('Segoe UI', 9),
                     bg=C['card'], fg=C['muted']).pack(anchor='w')

    def _page_install(self):
        self._page_title("⚙", "Instalando…",
                         "Por favor esperá, esto puede tardar unos minutos.")

        # Barra de progreso
        prog_card = self._card()
        prog_inner = tk.Frame(prog_card, bg=C['card'])
        prog_inner.pack(fill='x', padx=16, pady=14)

        self._prog_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Install.Horizontal.TProgressbar",
                        troughcolor=C['bg'],
                        background=C['accent'],
                        borderwidth=0,
                        thickness=18)
        self._progress = ttk.Progressbar(prog_inner,
                                         variable=self._prog_var,
                                         maximum=100, length=400,
                                         style="Install.Horizontal.TProgressbar")
        self._progress.pack(fill='x', pady=(0, 8))

        self._prog_label = tk.Label(prog_inner, text="Preparando…",
                                    font=('Segoe UI', 9),
                                    bg=C['card'], fg=C['muted'])
        self._prog_label.pack(anchor='w')

        # Log
        log_card = self._card()
        log_inner = tk.Frame(log_card, bg=C['card'])
        log_inner.pack(fill='both', expand=True, padx=16, pady=10)

        tk.Label(log_inner, text="Registro de instalación:",
                 font=('Segoe UI', 9, 'bold'),
                 bg=C['card'], fg=C['text']).pack(anchor='w', pady=(0, 4))

        log_scroll = tk.Scrollbar(log_inner)
        log_scroll.pack(side='right', fill='y')

        self._log_txt = tk.Text(log_inner,
                                font=('Consolas', 8),
                                bg='#111827', fg='#A8B4C5',
                                relief='flat', padx=8, pady=8,
                                height=8,
                                yscrollcommand=log_scroll.set,
                                state='disabled')
        self._log_txt.pack(side='left', fill='both', expand=True)
        log_scroll.configure(command=self._log_txt.yview)

        # Lanzar instalador en hilo
        self._installer = None
        self.after(200, self._start_install)

    def _append_log(self, msg):
        self._log_txt.configure(state='normal')
        self._log_txt.insert('end', msg + '\n')
        self._log_txt.see('end')
        self._log_txt.configure(state='disabled')

    def _set_progress(self, pct):
        self._prog_var.set(pct)
        self._prog_label.configure(text=f"{int(pct)}%  completado")

    def _start_install(self):
        if self.opt_reset_data.get():
            confirmar = messagebox.askyesno(
                "⚠️  Instalación limpia",
                "Esta opción ELIMINARÁ todos los datos existentes:\n"
                "base de datos, configuración y registros.\n\n"
                "¿Estás seguro? Esta acción no se puede deshacer.",
                icon='warning', parent=self
            )
            if not confirmar:
                return
        opts = {
            'shortcut_desktop': self.opt_desktop.get(),
            'shortcut_menu':    self.opt_menu.get(),
            'reset_data':       self.opt_reset_data.get(),
        }
        installer = Installer(self.install_dir.get(), opts)
        installer.on_step = lambda msg: self.after(0, self._append_log, msg)
        installer.on_prog = lambda p:   self.after(0, self._set_progress, p)
        self._installer = installer

        def run():
            ok, err = installer.run()
            self.after(0, self._install_done, ok, err)

        threading.Thread(target=run, daemon=True).start()

    def _install_done(self, ok, err):
        if ok:
            self._show_step(5)
        else:
            messagebox.showerror("Error de instalación",
                                 f"La instalación falló:\n\n{err}\n\n"
                                 "Revisá el registro para más detalles.",
                                 parent=self)
            self._show_step(3)   # Volver a opciones

    def _launch_app(self):
        app_dest = self._installer.app_dest if self._installer else self.install_dir.get()

        # Abrir la app via el lanzador .vbs usando os.startfile / ShellExecute.
        # Esto crea un proceso 100% independiente del installer (sin herencia de
        # variables PyInstaller como TCL_LIBRARY, TK_LIBRARY, _MEIPASS2, etc.)
        vbs = os.path.join(app_dest, "Lanzar TPV Elite.vbs")
        if os.path.exists(vbs):
            os.startfile(vbs)
            self.destroy()
            return

        # Fallback: lanzar pythonw.exe con entorno limpio
        try:
            py = python_exe()
        except RuntimeError:
            messagebox.showwarning(
                "Abrir aplicación",
                "No se pudo encontrar Python para abrir la aplicación.\n"
                "Abrila manualmente desde la carpeta de instalación.",
                parent=self,
            )
            self.destroy()
            return

        pythonw = os.path.join(os.path.dirname(py), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = py
        main = os.path.join(app_dest, "main.py")

        env = os.environ.copy()
        for key in ('TCL_LIBRARY', 'TK_LIBRARY', 'TCL_DATA',
                    '_MEIPASS2', 'PYINSTALLER_RESET_ENVIRONMENT'):
            env.pop(key, None)

        subprocess.Popen(
            [pythonw, main],
            cwd=app_dest,
            env=env,
            creationflags=subprocess.DETACHED_PROCESS,
        )
        self.destroy()

    def _page_done(self):
        box = tk.Frame(self.content, bg=C['bg'])
        box.place(relx=.5, rely=.4, anchor='center')

        tk.Label(box, text="✅", font=('Segoe UI', 52),
                 bg=C['bg']).pack()
        tk.Label(box, text="¡Instalación completada!",
                 font=('Segoe UI', 18, 'bold'),
                 bg=C['bg'], fg=C['success']).pack(pady=(12, 4))
        tk.Label(box,
                 text=f"{APP_NAME} se instaló correctamente en tu sistema.",
                 font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['muted']).pack()

        tk.Frame(box, bg=C['success'], height=3, width=80).pack(pady=14)

        tk.Label(box,
                 text=(
                     "• Abrí la app desde el acceso directo del Escritorio.\n"
                     "• La primera vez te pedirá configurar tu negocio.\n"
                     "• Podés desinstalar eliminando la carpeta de instalación."
                 ),
                 font=('Segoe UI', 10),
                 bg=C['bg'], fg=C['text'],
                 justify='left').pack(pady=(0, 22))

        # Botones de acción
        btn_row = tk.Frame(box, bg=C['bg'])
        btn_row.pack()

        tk.Button(btn_row, text="Terminar",
                  font=('Segoe UI', 10),
                  bg=C['card'], fg=C['text'],
                  bd=1, relief='flat',
                  padx=22, pady=9, cursor='hand2',
                  command=self.destroy).pack(side='left', padx=(0, 10))

        tk.Button(btn_row, text="Terminar y abrir la app  ▶",
                  font=('Segoe UI', 10, 'bold'),
                  bg=C['accent'], fg='white',
                  bd=0, relief='flat',
                  padx=22, pady=9, cursor='hand2',
                  command=self._launch_app).pack(side='left')


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Verificar que existe la carpeta app/
    if not os.path.isdir(app_source()):
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"No se encontró la carpeta 'app' junto al instalador.\n\nRuta esperada:\n{app_source()}",
            "Error del instalador",
            0x10  # MB_ICONERROR
        )
        sys.exit(1)

    app = SetupWizard()
    app.mainloop()
