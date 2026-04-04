import os
import subprocess
import tempfile
import uuid
import urllib.request

# ComfyUI specific imports
import folder_paths

# Ensure "video" is registered in folder_paths to prevent KeyErrors
if "video" not in folder_paths.folder_names_and_paths:
    # Use common video extensions
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv']
    # Default to the ComfyUI input directory
    input_dir = folder_paths.get_input_directory()
    folder_paths.folder_names_and_paths["video"] = ([input_dir], set(video_extensions))

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

class AutoCaptionsNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video_upload": (folder_paths.get_filename_list("video"), ),
                "run_mode": (["Burn Full Video", "Preview Style Only"], {"default": "Preview Style Only"}),
                "font_name": (POPULAR_FONTS, {"default": "Bangers"}),
                "font_size": ("INT", {"default": 72, "min": 8, "max": 256}),
                "primary_color": ("STRING", {"default": "#FFFFFF"}),
                "highlight_color": ("STRING", {"default": "#FFFF00"}),
                "alignment": (["Top-Left", "Top-Center", "Top-Right", "Mid-Left", "Mid-Center", "Mid-Right", "Bottom-Left", "Bottom-Center", "Bottom-Right"], {"default": "Bottom-Center"}),
                "platform_safe_zone": (["None", "TikTok", "IG Reels", "YT Shorts"], {"default": "None"}),
                "translate_to": (["Original", "English", "Spanish", "French", "German", "Italian", "Portuguese", "Japanese", "Chinese"], {"default": "Original"}),
            },
            "optional": {
                "video_path_override": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate_captions"
    OUTPUT_NODE = True
    CATEGORY = "Meisoft/Video"

    def extract_audio(self, video_path, output_audio_path):
        """Extracts audio from video using FFmpeg via subprocess."""
        command = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-i", video_path,
            "-vn",  # Disable video processing
            "-acodec", "pcm_s16le",  # Use PCM audio format
            "-ar", "16000",  # Set sample rate to 16kHz (optimal for Whisper)
            "-ac", "1",  # Set audio channels to 1 (mono)
            output_audio_path
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e.stderr.decode()}")
            return False

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
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int(round((seconds - int(seconds)) * 100))
        if centiseconds == 100:
            secs += 1
            centiseconds = 0

        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    def generate_ass_content(self, chunks, font_name, font_size, primary_color, highlight_color, alignment, platform_safe_zone):
        # 1. Translate Alignment
        align_map = {
            "Bottom-Left": 1, "Bottom-Center": 2, "Bottom-Right": 3,
            "Mid-Left": 4, "Mid-Center": 5, "Mid-Right": 6,
            "Top-Left": 7, "Top-Center": 8, "Top-Right": 9
        }
        ass_alignment = align_map.get(alignment, 2)

        # 2. Translate MarginV
        margin_map = {
            "TikTok": 250,
            "IG Reels": 200,
            "YT Shorts": 150,
            "None": 20
        }
        margin_v = margin_map.get(platform_safe_zone, 20)

        # Convert colors
        prim_ass = self.hex_to_ass_color(primary_color)
        high_ass = self.hex_to_ass_color(highlight_color)

        # Header setup
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name}, {font_size},{prim_ass},&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,3,1,{ass_alignment},20,20,{margin_v},1
Style: Emoji,Noto Color Emoji, {font_size},{prim_ass},&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,3,1,{ass_alignment},20,20,{margin_v},1

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

                    # Simpler approach matching user request:
                    word_tag = f"{{\\t({t_start_ms},{t_start_ms},\\c{high_ass}\\fscx120\\fscy120)\\t({t_start_ms},{t_end_ms},\\c{prim_ass}\\fscx100\\fscy100)}}"
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

    def generate_captions(self, video_upload, run_mode, font_name, font_size, primary_color, highlight_color, alignment, platform_safe_zone, translate_to, video_path_override=None):
        if video_path_override and isinstance(video_path_override, str) and video_path_override.strip() != "":
            video_path = video_path_override
        else:
            video_path = os.path.join(folder_paths.get_input_directory(), video_upload)

        if not video_path or not os.path.exists(video_path):
            print(f"Error: Video path '{video_path}' is invalid or does not exist.")
            return (video_path,)

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
        models_dir = os.path.join(current_dir, "models")
        os.makedirs(models_dir, exist_ok=True)

        # If Preview Style Only, skip audio extraction and whisper
        if run_mode == "Preview Style Only":
            print("Preview Mode: Skipping audio transcription...")
            # Fake chunk for preview
            chunks = [{
                "start": 1.0,
                "end": 3.0,
                "text": "TEST POP IN",
                "words": [
                    {"word": "TEST", "start": 1.0, "end": 1.5},
                    {"word": "POP", "start": 1.5, "end": 2.0},
                    {"word": "IN", "start": 2.0, "end": 3.0}
                ]
            }]

            # Generate ASS Content
            print("Generating ASS subtitles...")
            ass_content = self.generate_ass_content(
                chunks, font_name, font_size, primary_color, highlight_color, alignment, platform_safe_zone
            )

            # Save to ComfyUI temp directory
            temp_dir = folder_paths.get_temp_directory()
            temp_subs_filename = f"temp_subs_preview_{uuid.uuid4().hex[:8]}.ass"
            temp_subs_path = os.path.join(temp_dir, temp_subs_filename)

            with open(temp_subs_path, "w", encoding="utf-8") as f:
                f.write(ass_content)

            fonts_dir = self.download_font(font_name)
            escaped_subs_path = self.escape_ffmpeg_path(temp_subs_path)
            escaped_fonts_dir = self.escape_ffmpeg_path(fonts_dir)

            preview_filename = f"preview_{uuid.uuid4().hex[:8]}.jpg"
            preview_path = os.path.join(temp_dir, preview_filename)

            filter_str = f"subtitles='{escaped_subs_path}':fontsdir='{escaped_fonts_dir}'"

            ffmpeg_preview_cmd = [
                "ffmpeg",
                "-y",
                "-ss", "00:00:01.500",
                "-i", video_path,
                "-an",
                "-vf", filter_str,
                "-vframes", "1",
                "-q:v", "2",
                preview_path
            ]

            try:
                subprocess.run(ffmpeg_preview_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Preview generated at {preview_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error generating preview: {e.stderr.decode()}")

            ui_result = {
                "ui": {
                    "images": [
                        {
                            "filename": preview_filename,
                            "type": "temp"
                        }
                    ]
                },
                "result": ("",)
            }
            return ui_result


        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name

        try:
            print(f"Extracting audio from {video_path}...")
            success = self.extract_audio(video_path, temp_audio_path)

            if not success:
                return (video_path,)

            print("Loading Whisper model (base)...")
            try:
                # Load the model, downloading it to the custom models directory
                model = WhisperModel("base", device="cpu", compute_type="int8", download_root=models_dir)
            except Exception as e:
                print(f"Failed to load WhisperModel: {e}")
                return (video_path,)

            print("Transcribing audio...")
            whisper_task = "translate" if translate_to == "English" else "transcribe"
            segments, info = model.transcribe(temp_audio_path, word_timestamps=True, task=whisper_task)

            all_words = []
            for segment in segments:
                for word in segment.words:
                    all_words.append(word)

            print(f"Transcription complete. Total words found: {len(all_words)}")

            # Process chunks
            chunks = self.group_words_into_chunks(all_words, max_words=4)

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

            # Generate ASS Content
            print("Generating ASS subtitles...")
            ass_content = self.generate_ass_content(
                chunks, font_name, font_size, primary_color, highlight_color, alignment, platform_safe_zone
            )

            # Save to ComfyUI temp directory
            temp_dir = folder_paths.get_temp_directory()
            # Use uuid to avoid filename collision
            temp_subs_filename = f"temp_subs_{uuid.uuid4().hex[:8]}.ass"
            temp_subs_path = os.path.join(temp_dir, temp_subs_filename)

            with open(temp_subs_path, "w", encoding="utf-8") as f:
                f.write(ass_content)

            print(f"Subtitles successfully saved to: {temp_subs_path}")

            # Fetch font and format paths for FFmpeg
            fonts_dir = self.download_font(font_name)
            escaped_subs_path = self.escape_ffmpeg_path(temp_subs_path)
            escaped_fonts_dir = self.escape_ffmpeg_path(fonts_dir)

            # Generate Output Video Path
            output_dir = folder_paths.get_output_directory()
            final_video_filename = f"autocaptions_{uuid.uuid4().hex[:8]}.mp4"
            final_video_path = os.path.join(output_dir, final_video_filename)

            # FFmpeg Command to Burn Subtitles
            print(f"Burning subtitles to {final_video_path}...")
            # Use single quotes around the filter_complex string to safely handle spaces in paths on Unix/Windows
            # Note: in subprocess list format, we don't need external quotes around the whole filter string,
            # but internal spaces in the file path might need escaping if not handled by ffmpeg correctly.
            # Best practice for ffmpeg subtitles filter is to quote the filename if it has spaces, but escaping
            # works better across OS.
            filter_str = f"subtitles='{escaped_subs_path}':fontsdir='{escaped_fonts_dir}'"

            ffmpeg_burn_cmd = [
                "ffmpeg",
                "-y",
                "-i", video_path,
                "-vf", filter_str,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                "-crf", "19",
                "-c:a", "aac",
                "-b:a", "192k",
                final_video_path
            ]

            try:
                subprocess.run(ffmpeg_burn_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("Successfully generated final video.")
            except subprocess.CalledProcessError as e:
                print(f"Error burning subtitles: {e.stderr.decode()}")
                return (video_path,) # Fallback to original

            # Generate Preview Frame
            print("Generating preview frame...")
            preview_filename = f"preview_{uuid.uuid4().hex[:8]}.jpg"
            preview_path = os.path.join(temp_dir, preview_filename)

            ffmpeg_preview_cmd = [
                "ffmpeg",
                "-y",
                "-ss", "00:00:01.500",
                "-i", final_video_path,
                "-an",
                "-vframes", "1",
                "-q:v", "2",
                preview_path
            ]

            try:
                subprocess.run(ffmpeg_preview_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Preview generated at {preview_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error generating preview: {e.stderr.decode()}")
                # We can survive without a preview

            # Print output for monitoring
            print("\n--- Generated Chunks ---")
            for chunk in chunks:
                print(f"[{chunk['start']:.2f}s - {chunk['end']:.2f}s] {chunk['text']}")
            print("------------------------\n")

        finally:
            # Clean up temporary audio file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

        # Return dict format required by ComfyUI to draw the image, plus the result tuple
        ui_result = {
            "ui": {
                "images": [
                    {
                        "filename": preview_filename,
                        "type": "temp"
                    }
                ]
            },
            "result": (final_video_path,)
        }

        return ui_result
