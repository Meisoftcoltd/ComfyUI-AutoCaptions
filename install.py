import sys
import subprocess
import os
import shutil
import urllib.request

def install_requirements():
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        print("📦 [Meisoft Auto Captions] Instalando dependencias de Python...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
            print("✅ Dependencias de Python instaladas.")
        except Exception as e:
            print(f"❌ Error instalando dependencias: {e}")

def check_and_install_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("⚠️ [Meisoft Auto Captions] ADVERTENCIA CRÍTICA: FFmpeg NO está instalado.")
        if sys.platform.startswith("linux"):
            try:
                print("⚙️ Intentando instalar FFmpeg automáticamente (Linux/WSL)...")
                subprocess.check_call("sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg", shell=True)
                print("✅ FFmpeg instalado correctamente.")
            except Exception as e:
                print(f"❌ Falló la instalación automática de FFmpeg: {e}")
                print("👉 EJECUTA MANUALMENTE: sudo apt update && sudo apt install ffmpeg -y")
        elif sys.platform == "win32":
            print("👉 ACCIÓN REQUERIDA: Descarga FFmpeg para Windows y añádelo al PATH.")
    else:
        print("✅ [Meisoft Auto Captions] Motor FFmpeg detectado correctamente.")

def download_default_fonts():
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    os.makedirs(fonts_dir, exist_ok=True)

    default_fonts = {
        "Bangers-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf",
        "Anton-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
        "Montserrat-Black.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Black.ttf",
        "Oswald-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf",
        "PermanentMarker-Regular.ttf": "https://github.com/google/fonts/raw/main/apache/permanentmarker/PermanentMarker-Regular.ttf",
        "ComicNeue-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Bold.ttf"
    }

    print("🔠 [Meisoft Auto Captions] Comprobando fuentes por defecto...")
    for filename, url in default_fonts.items():
        filepath = os.path.join(fonts_dir, filename)
        if not os.path.exists(filepath):
            try:
                print(f"   -> Descargando {filename}...")
                urllib.request.urlretrieve(url, filepath)
            except Exception as e:
                print(f"   -> ❌ Error descargando {filename}: {e}")
    print("✅ Fuentes listas. Los usuarios pueden añadir sus propios archivos .ttf/.otf a la carpeta 'fonts/'.")

if __name__ == "__main__":
    print("🚀 Iniciando configuración de Meisoft Auto Captions...")
    install_requirements()
    check_and_install_ffmpeg()
    download_default_fonts()
    print("🎉 Configuración finalizada.")
