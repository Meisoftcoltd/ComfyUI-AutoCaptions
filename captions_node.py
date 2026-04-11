import os
import subprocess
import tempfile
import uuid
import urllib.request
import torch
import torchaudio
import numpy as np
import cv2
import re
import gc
import glob
from tqdm import tqdm

import folder_paths

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Warning: faster_whisper not found. Please ensure it is installed.")

# --- ESCANEO DINÁMICO DE FUENTES ---
def get_available_fonts():
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    # Busca fuentes TTF y OTF
    font_files = glob.glob(os.path.join(fonts_dir, "*.ttf")) + glob.glob(os.path.join(fonts_dir, "*.otf"))
    fonts = [os.path.splitext(os.path.basename(f))[0] for f in font_files]
    if not fonts:
        return ["Arial"] # Fallback de emergencia si la carpeta está vacía
    return sorted(fonts)

AVAILABLE_FONTS = get_available_fonts()
DEFAULT_FONT = AVAILABLE_FONTS[0] if AVAILABLE_FONTS else "Arial"

# --- MAPA DE COLORES AMPLIADO ---
COLOR_MAP = {
    "Blanco Puro": "#FFFFFF",
    "Amarillo Neón": "#FFFF00",
    "Verde Lima": "#00FF00",
    "Cian Eléctrico": "#00FFFF",
    "Rojo Intenso": "#FF0000",
    "Rosa Hot": "#FF00FF",
    "Naranja Vibrante": "#FFA500",
    "Negro Absoluto": "#000000",
    "Azul Océano": "#0000FF",
    "Morado Profundo": "#800080",
    "Oro Brillante": "#FFD700",
    "Plata": "#C0C0C0"
}

class AutoCaptionsNode:
    @classmethod
    def INPUT_TYPES(s):
        color_names = list(COLOR_MAP.keys())
        return {
            "required": {
                "images": ("IMAGE",),
                "audio": ("AUDIO",),
                "whisper_model": (["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo", "distil-large-v3"], {"default": "large-v3-turbo"}),
                "fps": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 120.0}),

                # --- Resolución de Diseño ---
                "width": ("INT", {"default": 1080, "min": 128, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1920, "min": 128, "max": 8192, "step": 8}),

                # --- Estilos de Fuente ---
                "font_name": (AVAILABLE_FONTS, {"default": DEFAULT_FONT}),
                "font_width_percent": ("INT", {"default": 80, "min": 10, "max": 200}),
                "max_words_per_line": ("INT", {"default": 4, "min": 1, "max": 15}),
                "outline_thickness": ("INT", {"default": 3, "min": 0, "max": 20}),
                "shadow_offset": ("INT", {"default": 5, "min": 0, "max": 20}),
                "text_casing": (["Normal", "Mayúsculas", "Capitalizado"], {"default": "Normal"}),
                "bold": ("BOOLEAN", {"default": False}),
                "italic": ("BOOLEAN", {"default": False}),

                # --- Colores y Posición ---
                "primary_color": (color_names, {"default": "Blanco Puro"}),
                "highlight_color": (color_names, {"default": "Amarillo Neón"}),
                "outline_color": (color_names, {"default": "Negro Absoluto"}),
                "shadow_color": (color_names, {"default": "Negro Absoluto"}),
                "alignment": (["Top-Left", "Top-Center", "Top-Right", "Mid-Left", "Mid-Center", "Mid-Right", "Bottom-Left", "Bottom-Center", "Bottom-Right"], {"default": "Bottom-Center"}),
                "platform_safe_zone": (["None", "TikTok", "IG Reels", "YT Shorts", "Facebook"], {"default": "None"}),
                "translate_to": (["Original", "English", "Spanish", "French", "German", "Italian", "Portuguese", "Japanese", "Chinese"], {"default": "Original"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "STRING", "STRING")
    RETURN_NAMES = ("images", "audio", "ass_file_path", "transcription_txt")
    FUNCTION = "generate_captions"
    CATEGORY = "Meisoft/Video"

    def hex_to_ass_color(self, hex_color):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6: return "&H00FFFFFF&"
        r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
        return f"&H00{b}{g}{r}&"

    def escape_ffmpeg_path(self, path):
        path = path.replace("\\", "/")
        path = path.replace(":", "\\:")
        return path

    def format_time_ass(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int(round((seconds - int(seconds)) * 100))
        if centiseconds == 100:
            secs += 1
            centiseconds = 0
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def generate_ass_content(self, chunks, font_name, font_size, primary_color, highlight_color, outline_color, shadow_color, alignment, platform_safe_zone, play_res_x, play_res_y, outline_thickness, shadow_offset, bold, italic):
        align_map = {
            "Bottom-Left": 1, "Bottom-Center": 2, "Bottom-Right": 3,
            "Mid-Left": 4, "Mid-Center": 5, "Mid-Right": 6,
            "Top-Left": 7, "Top-Center": 8, "Top-Right": 9
        }
        ass_alignment = align_map.get(alignment, 2)

        # --- ZONAS SEGURAS DINÁMICAS BASADAS EN PORCENTAJES ---
        is_bottom = alignment in ["Bottom-Left", "Bottom-Center", "Bottom-Right"]

        if is_bottom:
            if platform_safe_zone == "TikTok":
                margin_v = int(play_res_y * 0.27)  # 🚀 Subimos TikTok al 27% (flota sobre la descripción)
            elif platform_safe_zone == "Facebook":
                margin_v = int(play_res_y * 0.18)  # 📘 Facebook hereda el 18% (antiguo TikTok)
            elif platform_safe_zone == "IG Reels":
                margin_v = int(play_res_y * 0.15)  # 15% de margen inferior
            elif platform_safe_zone == "YT Shorts":
                margin_v = int(play_res_y * 0.12)  # 12% de margen inferior
            else:
                margin_v = 20  # Margen por defecto sin zona segura
        else:
            margin_v = 20
        # ------------------------------------------------------

        prim_ass = self.hex_to_ass_color(primary_color)
        high_ass = self.hex_to_ass_color(highlight_color)
        out_ass = self.hex_to_ass_color(outline_color)
        shad_ass = self.hex_to_ass_color(shadow_color)

        bold_val = -1 if bold else 0
        italic_val = -1 if italic else 0

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 1
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{prim_ass},&H000000FF&,{out_ass},{shad_ass},{bold_val},{italic_val},0,0,100,100,0,0,1,{outline_thickness},{shadow_offset},{ass_alignment},20,20,{margin_v},1
Style: Emoji,Noto Color Emoji,{font_size},{prim_ass},&H000000FF&,{out_ass},{shad_ass},{bold_val},{italic_val},0,0,100,100,0,0,1,{outline_thickness},{shadow_offset},{ass_alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for chunk in chunks:
            start_ass = self.format_time_ass(chunk["start"])
            end_ass = self.format_time_ass(chunk["end"])

            if chunk.get("is_translated"):
                line_text = f"{{\\c{prim_ass}\\fscx100\\fscy100}}{chunk['text']}"
            else:
                line_text = ""
                for i, word in enumerate(chunk["words"]):
                    duration_ms = int((word["end"] - word["start"]) * 1000)
                    t_start_ms = int((word["start"] - chunk["start"]) * 1000)
                    t_end_ms = int((word["end"] - chunk["start"]) * 1000)

                    t1, t2 = t_start_ms, t_start_ms + int(duration_ms * 0.15)
                    t3, t4 = t_start_ms + int(duration_ms * 0.85), t_end_ms

                    word_tag = f"{{\\t({t1},{t2},\\c{high_ass}\\fscx120\\fscy120)\\t({t3},{t4},\\c{prim_ass}\\fscx100\\fscy100)}}"
                    reset_tag = f"{{\\c{prim_ass}\\fscx100\\fscy100}}"
                    space = " " if i < len(chunk["words"]) - 1 else ""
                    line_text += f"{word_tag}{word['word'].strip()}{reset_tag}{space}"

            event = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{line_text}"
            events.append(event)

        return header + "\n".join(events) + "\n"

    def group_words_into_chunks(self, words, max_words=4):
        chunks = []
        current_chunk_words = []
        punctuation_marks = {'.', ',', '?', '!'}

        for word_info in words:
            word_text = word_info.word.strip()
            current_chunk_words.append({"word": word_text, "start": word_info.start, "end": word_info.end})

            has_punctuation = any(p in word_text for p in punctuation_marks)
            if len(current_chunk_words) >= max_words or has_punctuation:
                chunk_text = " ".join([w["word"] for w in current_chunk_words])
                chunks.append({"text": chunk_text, "start": current_chunk_words[0]["start"], "end": current_chunk_words[-1]["end"], "words": current_chunk_words})
                current_chunk_words = []

        if current_chunk_words:
            chunk_text = " ".join([w["word"] for w in current_chunk_words])
            chunks.append({"text": chunk_text, "start": current_chunk_words[0]["start"], "end": current_chunk_words[-1]["end"], "words": current_chunk_words})

        return chunks

    def generate_captions(self, images, audio, whisper_model, fps, width, height, font_name, font_width_percent, max_words_per_line, outline_thickness, shadow_offset, text_casing, bold, italic, primary_color, highlight_color, outline_color, shadow_color, alignment, platform_safe_zone, translate_to):

        real_primary = COLOR_MAP.get(primary_color, "#FFFFFF")
        real_highlight = COLOR_MAP.get(highlight_color, "#FFFF00")
        real_outline = COLOR_MAP.get(outline_color, "#000000")
        real_shadow = COLOR_MAP.get(shadow_color, "#000000")

        temp_subs_path = ""
        transcription_txt = ""

        if images is None or audio is None:
            return (images, audio, temp_subs_path, transcription_txt)

        batch_size, real_height, real_width, channels = images.shape

        models_dir = os.path.join(folder_paths.models_dir, "faster-whisper")
        os.makedirs(models_dir, exist_ok=True)
        temp_dir = folder_paths.get_temp_directory()
        fonts_dir = os.path.join(os.path.dirname(__file__), "fonts") # Carpeta local

        waveform = audio.get("waveform")
        sample_rate = audio.get("sample_rate", 16000)

        if waveform is None:
            return (images, audio, temp_subs_path, transcription_txt)
        if len(waveform.shape) == 3:
            waveform = waveform.squeeze(0)

        run_uuid = uuid.uuid4().hex[:8]
        temp_audio_path = os.path.join(temp_dir, f"temp_audio_{run_uuid}.wav")
        torchaudio.save(temp_audio_path, waveform, sample_rate)

        temp_subs_frames_dir = os.path.join(temp_dir, f"temp_subs_frames_{run_uuid}")
        os.makedirs(temp_subs_frames_dir, exist_ok=True)

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if torch.cuda.is_available() else "int8"
            print(f"Loading Whisper model ({whisper_model}) on {device} ({compute_type})...")

            try:
                model = WhisperModel(whisper_model, device=device, compute_type=compute_type, download_root=models_dir)
            except Exception as e:
                print(f"Failed to load WhisperModel: {e}")
                return (images, audio, temp_subs_path, transcription_txt)

            print("Transcribing audio...")
            whisper_task = "translate" if translate_to == "English" else "transcribe"
            segments, info = model.transcribe(
                temp_audio_path, word_timestamps=True, task=whisper_task, condition_on_previous_text=False
            )

            all_words = []
            for segment in segments:
                for word in segment.words:
                    all_words.append(word)

            print(f"Transcription complete. Total words found: {len(all_words)}")

            # ====== EVACUACIÓN DE VRAM (ANTI-KILLED) ======
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            # ===============================================

            chunks = self.group_words_into_chunks(all_words, max_words=max_words_per_line)

            if translate_to not in ["Original", "English"]:
                try:
                    from deep_translator import GoogleTranslator
                    lang_map = {"Spanish": "es", "French": "fr", "German": "de", "Italian": "it", "Portuguese": "pt", "Japanese": "ja", "Chinese": "zh-CN"}
                    target_lang = lang_map.get(translate_to, "en")
                    print(f"Translating to {translate_to} ({target_lang})...")
                    translator = GoogleTranslator(source='auto', target=target_lang)

                    for chunk in chunks:
                        chunk["text"] = translator.translate(chunk["text"])
                        chunk["is_translated"] = True
                except Exception as e:
                    print(f"Warning: Failed to translate: {e}")

            # ====== INICIO NUEVA LÓGICA DE TEXT CASING ======
            for chunk in chunks:
                if text_casing == "Mayúsculas":
                    chunk["text"] = chunk["text"].upper()
                    for w in chunk["words"]:
                        w["word"] = w["word"].upper()
                elif text_casing == "Capitalizado":
                    chunk["text"] = chunk["text"].title()
                    for w in chunk["words"]:
                        w["word"] = w["word"].title()
                # Si es "Normal", se deja tal cual lo entrega Whisper
            # ====== FIN NUEVA LÓGICA DE TEXT CASING ======

            # Generar Texto Plano
            transcription_txt = "\n".join([chunk['text'] for chunk in chunks])

            # Escalado basado en inputs width/height (Diseño UI)
            target_width = width * (font_width_percent / 100.0)
            calculated_font_size = max(12, int(target_width / (18 * 0.55)))

            # Limpieza para que coincida con la metadata interna de la fuente
            clean_font_name = font_name.replace("-Regular", "").replace("-Bold", "").replace("-Black", "")

            print(f"   -> 📏 Diseño Base: {width}x{height} | Target {font_width_percent}% | Size ASS: {calculated_font_size}")

            ass_content = self.generate_ass_content(
                chunks, clean_font_name, calculated_font_size, real_primary, real_highlight,
                real_outline, real_shadow, alignment, platform_safe_zone,
                width, height, outline_thickness, shadow_offset, bold, italic
            )

            temp_subs_path = os.path.join(temp_dir, f"temp_subs_{run_uuid}.ass")
            with open(temp_subs_path, "w", encoding="utf-8") as f:
                f.write(ass_content)

            escaped_subs_path = self.escape_ffmpeg_path(temp_subs_path)
            escaped_fonts_dir = self.escape_ffmpeg_path(fonts_dir)
            filter_str = f"subtitles='{escaped_subs_path}':fontsdir='{escaped_fonts_dir}':alpha=1"

            # FFmpeg renderiza usando el tamaño REAL del vídeo
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c=black@0.0:s={real_width}x{real_height}:r={fps},format=rgba",
                "-vf", f"{filter_str}",
                "-frames:v", str(batch_size),
                "-vcodec", "png",
                "-pix_fmt", "rgba",
                os.path.join(temp_subs_frames_dir, "sub_%05d.png")
            ]

            print(f"Generating transparent subtitle frames...")
            try:
                process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True)
                pbar = tqdm(total=batch_size, desc="🎬 Renderizando PNGs", unit="frame", dynamic_ncols=True)

                frame_pattern = re.compile(r"frame=\s*(\d+)")
                last_frame = 0
                for line in process.stderr:
                    match = frame_pattern.search(line)
                    if match:
                        current_frame = int(match.group(1))
                        frames_done = current_frame - last_frame
                        if frames_done > 0:
                            pbar.update(frames_done)
                            last_frame = current_frame

                process.wait()
                pbar.close()
                if process.returncode != 0:
                    return (images, audio, temp_subs_path, transcription_txt)
            except Exception as e:
                return (images, audio, temp_subs_path, transcription_txt)

            # ====== ANTI-KILLED: FUSIÓN DE BAJA MEMORIA ======
            print("Applying lossless Alpha Compositing (Low VRAM mode)...")

            # Creamos un tensor vacío en la CPU en lugar de clonar todo a VRAM
            out_images = torch.zeros_like(images, device="cpu")

            for i in range(batch_size):
                base_frame = images[i].cpu() # Aseguramos que trabajamos en CPU
                sub_frame_path = os.path.join(temp_subs_frames_dir, f"sub_{i+1:05d}.png")

                if os.path.exists(sub_frame_path):
                    sub_img_bgra = cv2.imread(sub_frame_path, cv2.IMREAD_UNCHANGED)

                    if sub_img_bgra is not None and sub_img_bgra.shape[2] == 4:
                        sub_img_rgba = cv2.cvtColor(sub_img_bgra, cv2.COLOR_BGRA2RGBA)
                        sub_tensor = torch.from_numpy(sub_img_rgba.astype(np.float32) / 255.0)

                        text_rgb = sub_tensor[:, :, :3]
                        alpha = sub_tensor[:, :, 3:4]

                        # Fusión matemática en CPU (Evita colapso de RAM)
                        out_images[i] = base_frame * (1.0 - alpha) + text_rgb * alpha

                        del sub_tensor, text_rgb, alpha, sub_img_bgra, sub_img_rgba
                    else:
                        out_images[i] = base_frame
                else:
                    out_images[i] = base_frame
            # =================================================

        finally:
            if os.path.exists(temp_audio_path):
                try: os.remove(temp_audio_path)
                except: pass
            if os.path.exists(temp_subs_frames_dir):
                import shutil
                try: shutil.rmtree(temp_subs_frames_dir)
                except: pass

        # Movemos de vuelta al dispositivo original solo al retornar
        return (out_images.to(images.device), audio, temp_subs_path, transcription_txt)
