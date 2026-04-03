from .captions_node import AutoCaptionsNode

NODE_CLASS_MAPPINGS = {
    "MeisoftAutoCaptions": AutoCaptionsNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MeisoftAutoCaptions": "🎬 Meisoft Auto Captions"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
