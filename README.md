# 🎬 ComfyUI Auto Captions (Meisoft)

¡Genera subtítulos dinámicos estilo CapCut/TikTok directamente en ComfyUI!

Este custom node utiliza la potencia de **Faster-Whisper** para la transcripción con precisión de palabras, y la magia de **FFmpeg** (`.ass` format) para quemar subtítulos espectaculares en tus vídeos. ¡Todo de forma automática, inteligente y sin salir de tu entorno de IA! 🚀

## ✨ Características

*   **⚡ Motor Ultra-Rápido:** Utiliza `faster-whisper` (modelo base/small) descargado directamente en el directorio del nodo, sin inundar la caché de tu sistema.
*   **🎤 Efecto Karaoke (Pop-in):** Sincronización precisa palabra por palabra. ¡Las palabras saltan (scale-up) y cambian de color justo cuando se pronuncian!
*   **🧠 Agrupación Inteligente:** Agrupa las palabras en bloques de lectura rápida (máximo 4 palabras por línea) y aplica cortes naturales de respiración respetando la puntuación (comas, puntos, etc.).
*   **🎨 Personalización Total:** Escoge la fuente, el color primario, el color de resalte (`highlight_color`), el tamaño y la alineación.
*   **📱 Zonas Seguras:** Integración directa de márgenes inteligentes para **TikTok**, **IG Reels** y **YT Shorts** para asegurar que el texto nunca quede oculto bajo la interfaz de la red social.
*   **🅰️ Fuentes Dinámicas:** Descarga la fuente que pidas automáticamente desde Google Fonts y hace un fallback a la fuente del sistema si ocurre un problema de red.

## 🛠️ Requisitos del Sistema

⚠️ **IMPORTANTE:** Este nodo **requiere que FFmpeg esté instalado en tu sistema** y añadido al `PATH` de las variables de entorno.

*   **Windows:** Descarga un build de [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) o usa `winget install ffmpeg`.
*   **macOS:** `brew install ffmpeg`
*   **Linux:** `sudo apt install ffmpeg`

## 📥 Instalación Manual

1. Ve a la carpeta de nodos personalizados de tu ComfyUI:
   ```bash
   cd ComfyUI/custom_nodes/
   ```
2. Clona este repositorio:
   ```bash
   git clone https://github.com/meisoftcoltd/ComfyUI-AutoCaptions.git
   ```
3. Entra en el directorio y descarga las dependencias del ecosistema Python:
   ```bash
   cd ComfyUI-AutoCaptions
   pip install -r requirements.txt
   ```
   *(Si usas el entorno portátil de Windows de ComfyUI, asegúrate de usar el pip de dicho entorno: `..\..\..\python_embeded\python.exe -m pip install -r requirements.txt`)*

4. ¡Reinicia ComfyUI!

> **📦 Próximamente en ComfyUI Manager:** Este nodo estará pronto disponible para su instalación directa con 1-click desde el listado oficial del ComfyUI Manager.

---
7. Ve a la página de GitHub del [repo original de ltdrdata](https://github.com/ltdrdata/ComfyUI-Manager) y abre un **Pull Request**. Una vez que el autor lo apruebe, el nodo estará disponible globalmente para todos los usuarios. 🎉
