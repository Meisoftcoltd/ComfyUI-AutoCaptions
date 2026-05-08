import sys
import os
from unittest.mock import MagicMock, patch

# Mock dependencies before importing from __init__
sys.modules["server"] = MagicMock()
sys.modules["aiohttp"] = MagicMock()
sys.modules["fontTools"] = MagicMock()
sys.modules["fontTools.ttLib"] = MagicMock()

import unittest
import importlib.util

# Add root to sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

def load_init_module():
    spec = importlib.util.spec_from_file_location("auto_captions_package", os.path.join(root_path, "__init__.py"))
    module = importlib.util.module_from_spec(spec)

    # Fake being a package
    module.__package__ = "auto_captions_package"
    sys.modules["auto_captions_package"] = module
    sys.modules["auto_captions_package.captions_node"] = MagicMock()

    # Mocking os.path.exists during module execution to skip initialization
    with patch('os.path.exists', return_value=False):
        spec.loader.exec_module(module)
    return module

init_mod = load_init_module()
optimize_font_names = init_mod.optimize_font_names

class TestOptimizeFontNames(unittest.TestCase):
    @patch('os.path.exists')
    @patch('os.remove')
    @patch('glob.glob')
    @patch('fontTools.ttLib.TTFont')
    def test_optimize_font_names_corrupt_file(self, mock_ttfont, mock_glob, mock_remove, mock_exists):
        """Test that a corrupt font file is deleted."""
        # Setup
        # glob.glob finds one ttf and one otf by default in the code
        # Let's make it return only one file total
        mock_glob.side_effect = [['fonts/corrupt.ttf'], []]
        mock_ttfont.side_effect = Exception("Corrupt font file")
        mock_exists.return_value = True

        # Execute
        optimize_font_names('fonts')

        # Verify
        mock_remove.assert_called_once_with('fonts/corrupt.ttf')

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('glob.glob')
    @patch('fontTools.ttLib.TTFont')
    def test_optimize_font_names_os_remove_error(self, mock_ttfont, mock_glob, mock_remove, mock_exists):
        """Test that OSError during file removal is handled gracefully."""
        # Setup
        mock_glob.side_effect = [['fonts/corrupt.ttf'], []]
        mock_ttfont.side_effect = Exception("Corrupt font file")
        mock_exists.return_value = True
        mock_remove.side_effect = OSError("Permission denied")

        # Execute
        # This should not raise OSError because of the try-except block in __init__.py
        try:
            optimize_font_names('fonts')
        except OSError:
            self.fail("optimize_font_names raised OSError unexpectedly!")

        # Verify
        mock_remove.assert_called_once_with('fonts/corrupt.ttf')

if __name__ == '__main__':
    unittest.main()
