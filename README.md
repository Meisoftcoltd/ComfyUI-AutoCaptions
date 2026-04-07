# 🎬 ComfyUI Auto Captions (Meisoft)

¡Genera subtítulos dinámicos estilo CapCut/TikTok directamente en ComfyUI!

Este custom node procesa de forma nativa los tensores de `IMAGE` y `AUDIO` de ComfyUI. Utiliza la potencia de **Faster-Whisper** para la transcripción con precisión de palabras, y la magia de **FFmpeg** (formato `.ass`) para quemar subtítulos espectaculares en tus vídeos. ¡Todo de forma automática, inteligente y sin salir de tu entorno de IA! 🚀

## ✨ Características Principales

*   **💎 Motor Lossless de Alpha Compositing:** Tus tensores originales jamás se comprimen. FFmpeg se usa exclusivamente para generar PNGs transparentes con los subtítulos, los cuales se fusionan matemáticamente con tus frames. ¡100% calidad visual garantizada!
*   **⚡ Motor Ultra-Rápido y Caché Inteligente:** Utiliza `faster-whisper` con un selector dinámico de modelos (`tiny` hasta los nuevos `large-v3-turbo` y `distil-large-v3`). Incluye un sistema anti-alucinaciones avanzado. Los modelos se guardan automáticamente en tu carpeta global de ComfyUI (`models/faster-whisper`) para compartir pesos y ahorrar espacio en disco.
*   **🎤 Efecto Karaoke (Pop-in):** Sincronización precisa palabra por palabra. ¡Las palabras presentan una animación de degradado suave (Fade In / Fade Out) en la que saltan (scale-up) y cambian al color de resalte justo cuando se pronuncian en inglés/original!
*   **🧠 Agrupación Inteligente:** Agrupa las palabras en bloques de lectura rápida (máximo 4 palabras por línea) y aplica cortes naturales de respiración forzando saltos de línea al encontrar puntuación fuerte (comas, puntos, etc.).
*   **🌍 Traducción Integrada:** Traduce tus subtítulos de forma automática a múltiples idiomas (Español, Francés, Alemán, Japonés, etc.) utilizando `deep-translator`.
*   **🅰️ Fuentes Dinámicas Inteligentes:** Ajuste automático del tamaño de la fuente basado en un porcentaje del ancho de tu video. Además, descarga dinámicamente tu fuente elegida desde Google Fonts.
*   **📱 Zonas Seguras (Safe Zones):** Márgenes integrados y precisos para **TikTok**, **IG Reels** y **YT Shorts** para asegurar que tu texto nunca quede oculto bajo la interfaz (botones de like, descripción) de la red social.
*   **🖥️ Previsualización de Grado Estudio:** El nodo cuenta con un canvas interactivo WYSIWYG. Verás un texto de marcador ("LOREM IPSUM DOLOR SIT") sobre un fondo cinematográfico que refleja en tiempo real tus ajustes de colores, fuentes, grosores y alineación (con una Safe Zone simulada del 10%).
*   **📊 Feedback Asíncrono:** Durante el renderizado de FFmpeg, no sufrirás cuelgues ni pantallas congeladas. Una barra de progreso profesional (`tqdm`) te mostrará en la terminal el frame actual, ETA y velocidad de procesamiento.

---

## 🎛️ Parámetros y Opciones del Nodo

El nodo `MeisoftAutoCaptions` acepta conexiones estándar de ComfyUI y ofrece una amplia gama de opciones de estilización.

### 🔌 Entradas (Inputs)
*   **`images`**: (`IMAGE`) El tensor de imágenes o secuencia de frames (tu video base).
*   **`audio`**: (`AUDIO`) El tensor de audio sincronizado con las imágenes.

### ⚙️ Configuraciones
*   **`fps`**: Los cuadros por segundo (Frames Per Second) a los que se exportará el video (Min: 1.0, Max: 120.0). *Debe coincidir con tus frames de entrada para mantener la sincronización.*
*   **`font_name`**: Selección entre decenas de las fuentes más populares de Google Fonts para subtítulos (e.g., Bangers, Montserrat, Anton, Bebas Neue).
*   **`font_width_percent`**: (10% - 100%) ¿Qué porcentaje de la pantalla debe ocupar el ancho de la línea de texto? El nodo calcula automáticamente el tamaño de fuente perfecto para lograr este porcentaje.
*   **`primary_color`**: El color base del texto cuando no está siendo pronunciado.
*   **`highlight_color`**: El color al que cambia la palabra exacta en el momento en que se pronuncia (Efecto Karaoke).
*   **`outline_color` / `outline_thickness`**: Color y grosor del contorno (stroke) alrededor del texto para darle legibilidad en fondos brillantes.
*   **`shadow_color` / `shadow_offset`**: Color y desplazamiento de una fuerte sombra paralela (Hard Drop Shadow) para darle un look 3D.
*   **`alignment`**: La ubicación física del texto en pantalla. Combina posiciones verticales y horizontales (Ej: `Bottom-Center`, `Top-Left`, `Mid-Right`).
*   **`platform_safe_zone`**: Aplica un margen vertical (Padding) automático desde el borde inferior/superior pensado para redes sociales:
    *   `None`: Margen estándar.
    *   `TikTok`: Margen muy alto para esquivar la descripción larga y los botones derechos.
    *   `IG Reels` / `YT Shorts`: Márgenes balanceados específicos para estas plataformas.
*   **`translate_to`**: Traduce lo que se escucha en el audio. Selecciona `Original` para transcribir en el mismo idioma del audio. (Nota: Si traduces, se desactiva el pop-in palabra por palabra en favor de subtítulos completos por frase).

### 📤 Salidas (Outputs)
*   **`images`**: (`IMAGE`) El tensor de imágenes con los subtítulos ya quemados de forma nativa.
*   **`audio`**: (`AUDIO`) Pasa el audio de entrada sin modificar.
*   **`ass_file_path`**: (`STRING`) La ruta del archivo `.ass` temporal generado, por si deseas usarlo en software de edición externo.

---

## 🛠️ Requisitos del Sistema

⚠️ **IMPORTANTE:** Este nodo procesa el video nativamente de una forma robusta, pero **requiere que FFmpeg esté instalado en tu sistema** y añadido al `PATH` de las variables de entorno.

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
