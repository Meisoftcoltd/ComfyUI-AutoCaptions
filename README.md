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

## 👨‍💻 Para Desarrolladores: Cómo publicar en ComfyUI Manager

Si eres el autor y deseas publicar este nodo en el repositorio oficial de **ComfyUI Manager**, sigue estos pasos:

1. Realiza un *Fork* del repositorio oficial de nodos: [ltdrdata/ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager).
2. Clona tu *fork* en tu computadora local.
3. Abre el archivo `custom-node-list.json`.
4. Añade un nuevo bloque de diccionario JSON al final de la lista con la información de este repositorio. El formato suele ser:
   ```json
   {
       "author": "Tu Nombre/Meisoft",
       "title": "🎬 Meisoft Auto Captions",
       "reference": "https://github.com/tu-usuario/ComfyUI-AutoCaptions",
       "files": ["https://github.com/tu-usuario/ComfyUI-AutoCaptions"],
       "install_type": "git-clone",
       "description": "Generador de subtítulos dinámicos y efecto karaoke palabra por palabra para ComfyUI usando Whisper y FFmpeg."
   }
   ```
5. Haz *Commit* de los cambios (`git commit -m "Add ComfyUI-AutoCaptions"`).
6. Haz *Push* a tu *fork*.
7. Ve a la página de GitHub del [repo original de ltdrdata](https://github.com/ltdrdata/ComfyUI-Manager) y abre un **Pull Request**. Una vez que el autor lo apruebe, el nodo estará disponible globalmente para todos los usuarios. 🎉
