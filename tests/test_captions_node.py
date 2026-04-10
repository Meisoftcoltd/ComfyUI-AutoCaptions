import sys
from unittest.mock import MagicMock
import pytest

# Mock modules to avoid ImportErrors during testing in restricted environment
sys.modules["torch"] = MagicMock()
sys.modules["torchaudio"] = MagicMock()
sys.modules["folder_paths"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["tqdm"] = MagicMock()

from captions_node import AutoCaptionsNode

def test_format_time_ass_basic():
    node = AutoCaptionsNode()
    assert node.format_time_ass(0) == "0:00:00.00"
    assert node.format_time_ass(1.23) == "0:00:01.23"
    assert node.format_time_ass(61.5) == "0:01:01.50"
    assert node.format_time_ass(3661.05) == "1:01:01.05"

def test_format_time_ass_rounding():
    node = AutoCaptionsNode()
    # 0.994 rounds down to .99
    assert node.format_time_ass(0.994) == "0:00:00.99"
    # 0.995 rounds up to 1.00
    assert node.format_time_ass(0.995) == "0:00:01.00"

def test_format_time_ass_overflow():
    node = AutoCaptionsNode()
    # 59.996 rounds up to 60.00, which should rollover to 1 minute
    assert node.format_time_ass(59.996) == "0:01:00.00"
    # 3599.996 rounds up to 3600.00, which should rollover to 1 hour
    assert node.format_time_ass(3599.996) == "1:00:00.00"

def test_format_time_ass_near_hour_overflow():
    node = AutoCaptionsNode()
    # 59 minutes, 59.996 seconds -> 1 hour
    assert node.format_time_ass(59 * 60 + 59.996) == "1:00:00.00"
