import os
import subprocess
import tempfile

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
                "video_path": ("STRING", {"default": ""}),
                "font_name": (POPULAR_FONTS, {"default": "Bangers"}),
                "font_size": ("INT", {"default": 72, "min": 8, "max": 256}),
                "primary_color": ("STRING", {"default": "#FFFFFF"}),
                "highlight_color": ("STRING", {"default": "#FFFF00"}),
                "alignment": (["Top-Left", "Top-Center", "Top-Right", "Mid-Left", "Mid-Center", "Mid-Right", "Bottom-Left", "Bottom-Center", "Bottom-Right"], {"default": "Bottom-Center"}),
                "platform_safe_zone": (["None", "TikTok", "IG Reels", "YT Shorts"], {"default": "None"}),
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

    def group_words_into_chunks(self, words, max_words=4):
        """
        Groups words into chunks of up to `max_words` length.
        Breaks early if strong punctuation is encountered.
        """
        chunks = []
        current_chunk = []
        punctuation_marks = {'.', ',', '?', '!'}

        for word_info in words:
            word_text = word_info.word.strip()
            current_chunk.append(word_info)

            # Check for early break due to punctuation
            has_punctuation = any(p in word_text for p in punctuation_marks)

            if len(current_chunk) >= max_words or has_punctuation:
                # Build the chunk data
                chunk_text = " ".join([w.word.strip() for w in current_chunk])
                start_time = current_chunk[0].start
                end_time = current_chunk[-1].end

                chunks.append({
                    "text": chunk_text,
                    "start": start_time,
                    "end": end_time
                })
                # Reset for the next chunk
                current_chunk = []

        # Add any remaining words as the final chunk
        if current_chunk:
            chunk_text = " ".join([w.word.strip() for w in current_chunk])
            start_time = current_chunk[0].start
            end_time = current_chunk[-1].end
            chunks.append({
                "text": chunk_text,
                "start": start_time,
                "end": end_time
            })

        return chunks

    def generate_captions(self, video_path, font_name, font_size, primary_color, highlight_color, alignment, platform_safe_zone):
        if not video_path or not os.path.exists(video_path):
            print(f"Error: Video path '{video_path}' is invalid or does not exist.")
            return (video_path,)

        # Define paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(current_dir, "models")
        os.makedirs(models_dir, exist_ok=True)

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
            segments, info = model.transcribe(temp_audio_path, word_timestamps=True)

            all_words = []
            for segment in segments:
                for word in segment.words:
                    all_words.append(word)

            print(f"Transcription complete. Total words found: {len(all_words)}")

            # Process chunks
            chunks = self.group_words_into_chunks(all_words, max_words=4)

            # Print output for monitoring
            print("\n--- Generated Chunks ---")
            for chunk in chunks:
                print(f"[{chunk['start']:.2f}s - {chunk['end']:.2f}s] {chunk['text']}")
            print("------------------------\n")

        finally:
            # Clean up temporary audio file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

        return (video_path,)
