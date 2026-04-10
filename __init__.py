import os
import server
from aiohttp import web
from .captions_node import AutoCaptionsNode

# --- SERVIDOR WEB DE FUENTES PARA LA INTERFAZ ---
# Esto permite que el navegador (JavaScript) pueda cargar las fuentes locales
fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
if os.path.exists(fonts_dir):
    server.PromptServer.instance.app.add_routes([
        web.static('/meisoft/fonts', fonts_dir)
    ])
# ------------------------------------------------

NODE_CLASS_MAPPINGS = {
    "MeisoftAutoCaptions": AutoCaptionsNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeisoftAutoCaptions": "🎬 Meisoft Auto Captions"
}

WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
