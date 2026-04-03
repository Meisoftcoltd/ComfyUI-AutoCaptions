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

    def generate_captions(self, video_path, font_name, font_size, primary_color, highlight_color, alignment, platform_safe_zone):
        # Placeholder functionality for Phase 1
        return (video_path,)
