import unittest
from unittest.mock import patch, MagicMock
import os
import re
import sys

# Mocking heavy dependencies
sys.modules["torch"] = MagicMock()
sys.modules["torchaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["tqdm"] = MagicMock()
sys.modules["folder_paths"] = MagicMock()

from captions_node import AutoCaptionsNode

class TestAutoCaptionsNodeSanitization(unittest.TestCase):
    def setUp(self):
        self.node = AutoCaptionsNode()

    @patch("urllib.request.urlretrieve")
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    def test_download_font_sanitization(self, mock_makedirs, mock_exists, mock_urlretrieve):
        test_cases = [
            ("../../malicious", "malicious"),
            ("Font Name With Spaces", "FontNameWithSpaces"),
            ("Special!@#$%^&*()Chars", "SpecialChars"),
            ("..\\..\\win_traversal", "wintraversal"),
            ("./current_dir", "currentdir"),
            ("", "Bangers"), # Fallback case
            ("!!!", "Bangers"), # Fallback case for non-alphanumeric
            ("Valid-Font-Name", "Valid-Font-Name"),
        ]

        for input_name, expected_formatted in test_cases:
            with self.subTest(input_name=input_name):
                self.node.download_font(input_name)

                # Check the path used in urlretrieve
                args, _ = mock_urlretrieve.call_args
                download_path = args[1]

                self.assertIn(f"{expected_formatted}-Regular.ttf", download_path)

                # Ensure it doesn't contain any dangerous sequences
                self.assertNotIn("..", download_path)
                self.assertNotIn("/", expected_formatted)
                self.assertNotIn("\\", expected_formatted)

    def test_hex_to_ass_color(self):
        self.assertEqual(self.node.hex_to_ass_color("#FFFFFF"), "&H00FFFFFF&")
        self.assertEqual(self.node.hex_to_ass_color("#FF0000"), "&H000000FF&") # RGB -> BGR
        self.assertEqual(self.node.hex_to_ass_color("#00FF00"), "&H0000FF00&")
        self.assertEqual(self.node.hex_to_ass_color("#0000FF"), "&H00FF0000&")
        self.assertEqual(self.node.hex_to_ass_color("invalid"), "&H00FFFFFF&")

if __name__ == "__main__":
    unittest.main()
