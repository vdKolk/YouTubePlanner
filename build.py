"""
Build script - maak een .exe van de applicatie
Voer uit met: python build.py
Of dubbelklik op: build.bat
"""

import subprocess
import sys
import os

PYINSTALLER_VERSION = "6.20.0"

def build():
    print("=" * 50)
    print("  YouTube Livestream Planner - Build naar .exe")
    print("=" * 50)
    print()

    if sys.version_info < (3, 9):
        print("FOUT: Python 3.9 of hoger is vereist.")
        print(f"  Huidige versie: {sys.version}")
        input("Druk op Enter om te sluiten...")
        sys.exit(1)

    print(f"Python versie: {sys.version.split()[0]}  OK")

    try:
        import PyInstaller
        current = PyInstaller.__version__
        if current != PYINSTALLER_VERSION:
            print(f"PyInstaller updaten naar {PYINSTALLER_VERSION}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", f"pyinstaller=={PYINSTALLER_VERSION}", "--quiet"],
                check=True
            )
    except ImportError:
        print(f"PyInstaller {PYINSTALLER_VERSION} installeren...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", f"pyinstaller=={PYINSTALLER_VERSION}", "--quiet"],
            check=True
        )

    print(f"PyInstaller {PYINSTALLER_VERSION}  OK")

    print("Afhankelijkheden installeren...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
        check=True
    )
    print("Afhankelijkheden  OK")
    print()
    print("Bouwen... (dit duurt 1-3 minuten)")
    print()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.ico")
    has_icon = os.path.exists(icon_path)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "YouTubePlanner",
        "--add-data", f"assets{os.pathsep}assets",
        "--hidden-import", "customtkinter",
        "--hidden-import", "zoneinfo",
        "--hidden-import", "tzdata",
        "--hidden-import", "google.auth.transport.requests",
        "--hidden-import", "google_auth_oauthlib.flow",
        "--hidden-import", "googleapiclient.discovery",
        "--collect-all", "customtkinter",
        "--collect-all", "tzdata",
        "main.py",
    ]

    if has_icon:
        cmd += ["--icon", icon_path]

    result = subprocess.run(cmd, cwd=base_dir)

    print()
    if result.returncode == 0:
        print("=" * 50)
        print("  BUILD GESLAAGD!")
        print("=" * 50)
        print()
        print("  Bestand: dist\\YouTubePlanner.exe")
        print()
        print("  Instructies:")
        print("  1. Kopieer YouTubePlanner.exe naar gewenste locatie")
        print("  2. Instellingen worden opgeslagen naast het .exe bestand")
        print()
    else:
        print("=" * 50)
        print("  BUILD MISLUKT - zie foutmelding hierboven")
        print("=" * 50)
        print()

    input("Druk op Enter om te sluiten...")


if __name__ == "__main__":
    build()
