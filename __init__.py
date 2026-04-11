import os
import glob
import re
import server
from aiohttp import web
from .captions_node import AutoCaptionsNode

# --- MOTOR DE OPTIMIZACIÓN DE FUENTES (Sin Anestesia) ---
def optimize_font_names(fonts_dir):
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("⚠️ [Meisoft Auto Captions] 'fonttools' no instalado. Omitiendo limpieza profunda.")
        return

    print("🔠 [Meisoft Auto Captions] Iniciando auditoría de fuentes...")
    # Buscamos archivos ttf y otf
    font_files = glob.glob(os.path.join(fonts_dir, "*.ttf")) + glob.glob(os.path.join(fonts_dir, "*.otf"))

    for filepath in font_files:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        try:
            # Intentamos abrir la fuente para leer sus metadatos
            font = TTFont(filepath)

            # --- NUEVA COMPROBACIÓN DE INTEGRIDAD ---
            # Verificamos si tiene la tabla de mapeo (cmap) y datos de dibujo (glyf o CFF)
            if not ('cmap' in font and ('glyf' in font or 'CFF ' in font)):
                print(f"   -> 💀 Fuente sin glifos válidos (Incompatible): Eliminando '{filename}'...")
                font.close()
                os.remove(filepath)
                continue
            # ----------------------------------------

            name_record = font['name']
            internal_name = None

            # Buscamos el Nombre Completo (ID 4) o la Familia (ID 1)
            for record in name_record.names:
                if record.nameID in (4, 1):
                    # Convertimos a string usable
                    internal_name = record.toUnicode()
                    if record.nameID == 4: break
            font.close()

            if internal_name:
                # Limpiamos caracteres prohibidos en sistemas de archivos
                clean_name = re.sub(r'[<>:"/\\|?*]', '', internal_name).strip()
                new_filename = f"{clean_name}{ext}"
                new_filepath = os.path.join(fonts_dir, new_filename)

                # Caso A: El archivo ya está perfecto
                if filename == new_filename:
                    continue

                # Caso B: Ya existe otro archivo con ese nombre real (Duplicado)
                if os.path.exists(new_filepath):
                    print(f"   -> 🗑️ Duplicado detectado: Eliminando '{filename}'...")
                    os.remove(filepath)
                else:
                    # Caso C: Renombrado al nombre real que pide FFmpeg
                    print(f"   -> 🏷️ Renombrando: '{filename}' -> '{new_filename}'")
                    os.rename(filepath, new_filepath)
            else:
                # Si no tiene nombre interno, es un archivo basura
                print(f"   -> 💀 Fuente sin metadatos: Eliminando '{filename}'...")
                os.remove(filepath)

        except Exception as e:
            # Si falla al abrirse (Corrupto), se elimina sin preguntar
            print(f"   -> 🧨 ARCHIVO CORRUPTO DETECTADO: Eliminando '{filename}'... (Error: {e})")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass

# --- INICIALIZACIÓN DEL SERVIDOR ---
fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
if os.path.exists(fonts_dir):
    # 1. Ejecutar limpieza antes de que el JS intente cargar nada
    optimize_font_names(fonts_dir)

    # 2. Registrar la ruta estática para la interfaz
    server.PromptServer.instance.app.add_routes([
        web.static('/meisoft/fonts', fonts_dir)
    ])

NODE_CLASS_MAPPINGS = {
    "MeisoftAutoCaptions": AutoCaptionsNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeisoftAutoCaptions": "🎬 Meisoft Auto Captions"
}

WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']