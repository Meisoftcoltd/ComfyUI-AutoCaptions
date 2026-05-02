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
from tqdm import tqdm

# ComfyUI specific imports
import folder_paths

# We will import faster_whisper conditionally or at the top level
try:
    from faster_whisper import WhisperModel
except ImportError:
    # If the user doesn't have faster_whisper installed, we will handle it or let it fail with a clear message
    print("Warning: faster_whisper not found. Please ensure it is installed.")


POPULAR_FONTS = [
    "Bangers", "Anton", "Montserrat", "Roboto Black", "Oswald", "Poppins",
    "Knewave", "Luckiest Guy", "Impact", "Bebas Neue", "Lobster",
    "Permanent Marker", "Alfa Slab One", "Oleo Script", "Fredoka One",
    "Righteous", "Passion One", "Titan One", "Fjalla One", "Patua One",
    "Concert One", "Changa", "Carter One", "Sigmar One", "Chewy",
    "Russo One", "Lilita One", "Black Ops One", "Vampiro One", "Rubik Mono One",
    "Bungee", "Squada One", "Monoton", "Bowlby One", "Baloo 2", "Creepster"
]

COLOR_MAP = {
    "Blanco Puro": "#FFFFFF",
    "Amarillo Neón": "#FFFF00",
    "Verde Lima": "#00FF00",
    "Cian Eléctrico": "#00FFFF",
    "Rojo Intenso": "#FF0000",
    "Rosa Hot": "#FF00FF",
    "Naranja Vibrante": "#FFA500",
    "Negro Absoluto": "#000000"
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
                "font_name": (POPULAR_FONTS, {"default": "Bangers"}),
                "font_width_percent": ("INT", {"default": 80, "min": 10, "max": 200}),
                "max_words_per_line": ("INT", {"default": 4, "min": 1, "max": 15}),
                "outline_thickness": ("INT", {"default": 3, "min": 0, "max": 20}),
                "shadow_offset": ("INT", {"default": 5, "min": 0, "max": 20}),
                "primary_color": (color_names, {"default": "Blanco Puro"}),
                "highlight_color": (color_names, {"default": "Amarillo Neón"}),
                "outline_color": (color_names, {"default": "Negro Absoluto"}),
                "shadow_color": (color_names, {"default": "Negro Absoluto"}),
                "alignment": (["Top-Left", "Top-Center", "Top-Right", "Mid-Left", "Mid-Center", "Mid-Right", "Bottom-Left", "Bottom-Center", "Bottom-Right"], {"default": "Bottom-Center"}),
                "platform_safe_zone": (["None", "TikTok", "IG Reels", "YT Shorts"], {"default": "None"}),
                "translate_to": (["Original", "English", "Spanish", "French", "German", "Italian", "Portuguese", "Japanese", "Chinese"], {"default": "Original"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "STRING")
    RETURN_NAMES = ("images", "audio", "ass_file_path")
    FUNCTION = "generate_captions"
    CATEGORY = "Meisoft/Video"

    def hex_to_ass_color(self, hex_color):
        """Converts #RRGGBB to &HBBGGRR&."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return "&H00FFFFFF&" # Fallback to white

        r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
        return f"&H00{b}{g}{r}&"

    def download_font(self, font_name):
        """
        Downloads a font from the Google Fonts raw GitHub repo.
        Falls back gracefully if the download fails.
        Returns the path to the directory containing the font.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(current_dir, "fonts")
        os.makedirs(fonts_dir, exist_ok=True)

        # Remove spaces for filename, lowercase for URL path, etc.
        # Note: Google fonts directory paths and names can be complex. We'll use a best-effort approach.
        formatted_name = font_name.replace(" ", "")
        font_filename = f"{formatted_name}-Regular.ttf"
        font_path = os.path.join(fonts_dir, font_filename)

        if os.path.exists(font_path):
            return fonts_dir

        # Attempt to download
        url_name_lower = formatted_name.lower()
        # Common repositories (ofl, ufl, apache)
        urls_to_try = [
            f"https://github.com/google/fonts/raw/main/ofl/{url_name_lower}/{font_filename}",
            f"https://github.com/google/fonts/raw/main/apache/{url_name_lower}/{font_filename}",
            f"https://github.com/google/fonts/raw/main/ufl/{url_name_lower}/{font_filename}"
        ]

        print(f"Downloading font: {font_name}...")
        for url in urls_to_try:
            try:
                urllib.request.urlretrieve(url, font_path)
                print(f"Successfully downloaded font from {url}")
                return fonts_dir
            except Exception as e:
                continue

        print(f"Warning: Failed to download font '{font_name}'. Falling back to system defaults.")
        # Return fonts_dir anyway; FFmpeg will use fallback system fonts if the specific TTF is missing
        return fonts_dir

    def escape_ffmpeg_path(self, path):
        """Escapes Windows paths for FFmpeg's subtitles filter."""
        # Replace backslashes with forward slashes
        path = path.replace("\\", "/")
        # Escape colon (e.g., C:/ -> C\:/)
        path = path.replace(":", "\\:")
        return path

    def format_time_ass(self, seconds):
        """Formats seconds to ASS time format: H:MM:SS.cs"""
        # Round to 2 decimal places to handle centiseconds correctly
        total_centiseconds = int(round(seconds * 100))

        centiseconds = total_centiseconds % 100
        total_seconds = total_centiseconds // 100

        secs = total_seconds % 60
        total_minutes = total_seconds // 60

        minutes = total_minutes % 60
        hours = total_minutes // 60

        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def generate_ass_content(self, chunks, font_name, font_size, primary_color, highlight_color, outline_color, shadow_color, alignment, platform_safe_zone, play_res_x, play_res_y, outline_thickness, shadow_offset):
        # 1. Translate Alignment
        align_map = {
            "Bottom-Left": 1, "Bottom-Center": 2, "Bottom-Right": 3,
            "Mid-Left": 4, "Mid-Center": 5, "Mid-Right": 6,
            "Top-Left": 7, "Top-Center": 8, "Top-Right": 9
        }
        ass_alignment = align_map.get(alignment, 2)

        # 2. Translate MarginV (Solo para Bottom)
        margin_map = {
            "TikTok": 250,
            "IG Reels": 200,
            "YT Shorts": 150,
            "None": 20
        }
        is_bottom = alignment in ["Bottom-Left", "Bottom-Center", "Bottom-Right"]
        margin_v = margin_map.get(platform_safe_zone, 20) if is_bottom else 20

        # Convert colors
        prim_ass = self.hex_to_ass_color(primary_color)
        high_ass = self.hex_to_ass_color(highlight_color)
        out_ass = self.hex_to_ass_color(outline_color)
        shad_ass = self.hex_to_ass_color(shadow_color)

        # Header setup
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 1
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name}, {font_size},{prim_ass},&H000000FF&,{out_ass},{shad_ass},0,0,0,0,100,100,0,0,1,{outline_thickness},{shadow_offset},{ass_alignment},20,20,{margin_v},1
Style: Emoji,Noto Color Emoji, {font_size},{prim_ass},&H000000FF&,{out_ass},{shad_ass},0,0,0,0,100,100,0,0,1,{outline_thickness},{shadow_offset},{ass_alignment},20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        for chunk in chunks:
            start_ass = self.format_time_ass(chunk["start"])
            end_ass = self.format_time_ass(chunk["end"])

            if chunk.get("is_translated"):
                # If translated via deep-translator, we lose word-level timestamps.
                # Just output the translated text spanning the chunk's duration in primary color.
                line_text = f"{{\\c{prim_ass}\\fscx100\\fscy100}}{chunk['text']}"
            else:
                # Reconstruct the line with karaoke tags
                line_text = ""
                for i, word in enumerate(chunk["words"]):
                    # Calculate duration in milliseconds for the transition tag
                    duration_ms = int((word["end"] - word["start"]) * 1000)

                    t_start_ms = int((word["start"] - chunk["start"]) * 1000)
                    t_end_ms = int((word["end"] - chunk["start"]) * 1000)

                    # Tiempos del degradado (15% in, 70% hold, 15% out)
                    t1 = t_start_ms
                    t2 = t_start_ms + int(duration_ms * 0.15)
                    t3 = t_start_ms + int(duration_ms * 0.85)
                    t4 = t_end_ms

                    # Tag ASS con doble transición (Fade IN y Fade OUT)
                    word_tag = f"{{\\t({t1},{t2},\\c{high_ass}\\fscx120\\fscy120)\\t({t3},{t4},\\c{prim_ass}\\fscx100\\fscy100)}}"
                    reset_tag = f"{{\\c{prim_ass}\\fscx100\\fscy100}}"

                    space = " " if i < len(chunk["words"]) - 1 else ""
                    line_text += f"{word_tag}{word['word'].strip()}{reset_tag}{space}"

            event = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{line_text}"
            events.append(event)

        return header + "\n".join(events) + "\n"

    def group_words_into_chunks(self, words, max_words=4):
        """
        Groups words into chunks of up to `max_words` length.
        Breaks early if strong punctuation is encountered.
        """
        chunks = []
        current_chunk_words = []
        punctuation_marks = {'.', ',', '?', '!'}

        for word_info in words:
            word_text = word_info.word.strip()
            current_chunk_words.append({
                "word": word_text,
                "start": word_info.start,
                "end": word_info.end
            })

            # Check for early break due to punctuation
            has_punctuation = any(p in word_text for p in punctuation_marks)

            if len(current_chunk_words) >= max_words or has_punctuation:
                # Build the chunk data
                chunk_text = " ".join([w["word"] for w in current_chunk_words])
                start_time = current_chunk_words[0]["start"]
                end_time = current_chunk_words[-1]["end"]

                chunks.append({
                    "text": chunk_text,
                    "start": start_time,
                    "end": end_time,
                    "words": current_chunk_words
                })
                # Reset for the next chunk
                current_chunk_words = []

        # Add any remaining words as the final chunk
        if current_chunk_words:
            chunk_text = " ".join([w["word"] for w in current_chunk_words])
            start_time = current_chunk_words[0]["start"]
            end_time = current_chunk_words[-1]["end"]
            chunks.append({
                "text": chunk_text,
                "start": start_time,
                "end": end_time,
                "words": current_chunk_words
            })

        return chunks

    def generate_captions(self, images, audio, whisper_model, fps, font_name, font_width_percent, max_words_per_line, outline_thickness, shadow_offset, primary_color, highlight_color, outline_color, shadow_color, alignment, platform_safe_zone, translate_to):

        real_primary = COLOR_MAP.get(primary_color, "#FFFFFF")
        real_highlight = COLOR_MAP.get(highlight_color, "#FFFF00")
        real_outline = COLOR_MAP.get(outline_color, "#000000")
        real_shadow = COLOR_MAP.get(shadow_color, "#000000")

        if images is None or audio is None:
            print("Error: Required inputs (images, audio) are missing.")
            return (images, audio, "")

        # Extract dimensions from images tensor [B, H, W, C]
        batch_size, height, width, channels = images.shape

        # Language map for deep-translator
        lang_map = {
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Portuguese": "pt",
            "Japanese": "ja",
            "Chinese": "zh-CN"
        }

        # Define paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(folder_paths.models_dir, "faster-whisper")
        os.makedirs(models_dir, exist_ok=True)

        temp_dir = folder_paths.get_temp_directory()

        # Handle Audio extraction via torchaudio
        print("Extracting audio tensor to temp file...")
        waveform = audio.get("waveform")
        sample_rate = audio.get("sample_rate", 16000)

        if waveform is None:
            print("Error: Audio tensor does not contain 'waveform'.")
            return (images, audio, "")

        if len(waveform.shape) == 3:
            waveform = waveform.squeeze(0) # Remove batch dimension: [B, C, S] -> [C, S]

        # Use uuid to avoid filename collision
        run_uuid = uuid.uuid4().hex[:8]
        temp_audio_path = os.path.join(temp_dir, f"temp_audio_{run_uuid}.wav")

        try:
            torchaudio.save(temp_audio_path, waveform, sample_rate)
        except Exception as e:
            print(f"Error saving audio tensor: {e}")
            return (images, audio, "")

        # For Alpha Compositing: Create a temporary directory to hold FFmpeg generated PNGs
        temp_subs_frames_dir = os.path.join(temp_dir, f"temp_subs_frames_{run_uuid}")
        os.makedirs(temp_subs_frames_dir, exist_ok=True)

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if torch.cuda.is_available() else "int8"
            print(f"Loading Whisper model ({whisper_model}) on {device} ({compute_type})...")
            try:
                # Load the model, downloading it to the custom models directory
                model = WhisperModel(whisper_model, device=device, compute_type=compute_type, download_root=models_dir)
            except Exception as e:
                print(f"Failed to load WhisperModel: {e}")
                return (images, audio, "")

            print("Transcribing audio...")
            whisper_task = "translate" if translate_to == "English" else "transcribe"
            segments, _ = model.transcribe(
                temp_audio_path,
                word_timestamps=True,
                task=whisper_task,
                condition_on_previous_text=False
            )

            all_words = []
            for segment in segments:
                for word in segment.words:
                    all_words.append(word)

            print(f"Transcription complete. Total words found: {len(all_words)}")

            # Process chunks
            chunks = self.group_words_into_chunks(all_words, max_words=max_words_per_line)

            # Handle non-English translation via deep-translator
            if translate_to not in ["Original", "English"]:
                try:
                    from deep_translator import GoogleTranslator
                    target_lang = lang_map.get(translate_to, "en")
                    print(f"Translating to {translate_to} ({target_lang})...")
                    translator = GoogleTranslator(source='auto', target=target_lang)

                    for chunk in chunks:
                        translated_text = translator.translate(chunk["text"])
                        chunk["text"] = translated_text
                        chunk["is_translated"] = True
                except Exception as e:
                    print(f"Warning: Failed to translate to {translate_to}: {e}. Falling back to original transcription.")

            # Auto-escalado de fuente basado en el ancho del lienzo
            target_width = width * (font_width_percent / 100.0)
            estimated_chars_per_line = 18 # Promedio para chunks de 4 palabras

            # Multiplicador x2.0 porque ASS toma el font_size como altura, no como anchura.
            calculated_font_size = int((target_width * 2.0) / (estimated_chars_per_line * 0.55))

            # Mínimo de seguridad para evitar errores en FFmpeg
            calculated_font_size = max(12, calculated_font_size)

            print(f"   -> 📏 Auto-ajuste de fuente: Lienzo {width}px | Meta {font_width_percent}% | Tamaño final ASS: {calculated_font_size}")

            # Generate ASS Content
            print("Generating ASS subtitles...")
            ass_content = self.generate_ass_content(
                chunks, font_name, calculated_font_size, real_primary, real_highlight, real_outline, real_shadow, alignment, platform_safe_zone, width, height, outline_thickness, shadow_offset
            )

            # Save to ComfyUI temp directory
            # Use uuid to avoid filename collision
            temp_subs_filename = f"temp_subs_{run_uuid}.ass"
            temp_subs_path = os.path.join(temp_dir, temp_subs_filename)

            with open(temp_subs_path, "w", encoding="utf-8") as f:
                f.write(ass_content)

            print(f"Subtitles successfully saved to: {temp_subs_path}")

            # Fetch font and format paths for FFmpeg
            fonts_dir = self.download_font(font_name)
            escaped_subs_path = self.escape_ffmpeg_path(temp_subs_path)
            escaped_fonts_dir = self.escape_ffmpeg_path(fonts_dir)

            # FFmpeg Command to generate transparent PNG sequence
            filter_str = f"subtitles='{escaped_subs_path}':fontsdir='{escaped_fonts_dir}':alpha=1"

            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                # Forzamos format=rgba directamente en el lienzo generador
                "-i", f"color=c=black@0.0:s={width}x{height}:r={fps},format=rgba",
                "-vf", f"{filter_str}",
                "-frames:v", str(batch_size),
                "-vcodec", "png",
                # Obligamos al encoder PNG a guardar el canal Alpha
                "-pix_fmt", "rgba",
                os.path.join(temp_subs_frames_dir, "sub_%05d.png")
            ]

            # FFmpeg Command Execution con barra de progreso
            print(f"Generating transparent subtitle frames to {temp_subs_frames_dir}...")

            try:
                # Usamos Popen para leer la salida línea por línea en tiempo real
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    universal_newlines=True
                )

                # Barra de progreso profesional apuntando al total de frames
                pbar = tqdm(total=batch_size, desc="🎬 Renderizando Subtítulos (PNG)", unit="frame", dynamic_ncols=True)

                # Expresión regular para cazar el frame actual en el output de FFmpeg
                frame_pattern = re.compile(r"frame=\s*(\d+)")
                last_frame = 0

                # Leemos el stderr de FFmpeg (donde escupe el progreso)
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
                    print(f"Error generating subtitles: FFmpeg returned code {process.returncode}")
                    return (images, audio, "") # Fallback a la imagen original si falla

                print("Successfully generated subtitle frames.")

            except Exception as e:
                print(f"Error executing FFmpeg: {e}")
                return (images, audio, "")

            # Alpha Compositing 100% PyTorch Native
            print("Applying lossless Alpha Compositing on GPU/CPU...")
            out_images = images.clone()
            device = out_images.device # Identificamos dónde vive el tensor (ej. 'cuda:0')

            for i in range(batch_size):
                sub_frame_path = os.path.join(temp_subs_frames_dir, f"sub_{i+1:05d}.png")

                if os.path.exists(sub_frame_path):
                    # Leemos la imagen (BGRA) con OpenCV
                    sub_img_bgra = cv2.imread(sub_frame_path, cv2.IMREAD_UNCHANGED)

                    if sub_img_bgra is not None and sub_img_bgra.shape[2] == 4:
                        # Convertir BGRA a RGBA
                        sub_img_rgba = cv2.cvtColor(sub_img_bgra, cv2.COLOR_BGRA2RGBA)

                        # Convertir directamente a Tensor y moverlo al mismo dispositivo que el video
                        sub_tensor = torch.from_numpy(sub_img_rgba.astype(np.float32) / 255.0).to(device)

                        # Separar RGB y Alpha [H, W, 1]
                        text_rgb = sub_tensor[:, :, :3]
                        alpha = sub_tensor[:, :, 3:4]

                        # Fusión matemática nativa en PyTorch
                        out_images[i] = out_images[i] * (1.0 - alpha) + text_rgb * alpha

            # Print output for monitoring
            print("\n--- Generated Chunks ---")
            for chunk in chunks:
                print(f"[{chunk['start']:.2f}s - {chunk['end']:.2f}s] {chunk['text']}")
            print("------------------------\n")

        finally:
            # Clean up temporary audio file and frames directory
            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

            if os.path.exists(temp_subs_frames_dir):
                import shutil
                try:
                    shutil.rmtree(temp_subs_frames_dir)
                except Exception:
                    pass

        return (out_images, audio, temp_subs_path)
