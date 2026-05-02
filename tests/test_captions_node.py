import sys
from unittest.mock import MagicMock

# Mock dependencies before importing the node
sys.modules["torch"] = MagicMock()
sys.modules["torchaudio"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["folder_paths"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["tqdm"] = MagicMock()

import unittest
from unittest.mock import patch
from captions_node import AutoCaptionsNode

class WordInfo:
    def __init__(self, word, start, end):
        self.word = word
        self.start = start
        self.end = end

class TestAutoCaptionsNode(unittest.TestCase):
    def setUp(self):
        self.node = AutoCaptionsNode()

    def test_group_words_into_chunks_basic(self):
        words = [
            WordInfo("Hello", 0.0, 0.5),
            WordInfo("world", 0.5, 1.0),
            WordInfo("this", 1.0, 1.5),
            WordInfo("is", 1.5, 2.0),
            WordInfo("a", 2.0, 2.5),
            WordInfo("test", 2.5, 3.0),
        ]
        # max_words = 4
        chunks = self.node.group_words_into_chunks(words, max_words=4)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["text"], "Hello world this is")
        self.assertEqual(chunks[1]["text"], "a test")
        self.assertEqual(chunks[0]["start"], 0.0)
        self.assertEqual(chunks[0]["end"], 2.0)
        self.assertEqual(chunks[1]["start"], 2.0)
        self.assertEqual(chunks[1]["end"], 3.0)
        self.assertEqual(len(chunks[0]["words"]), 4)
        self.assertEqual(len(chunks[1]["words"]), 2)

    def test_group_words_into_chunks_punctuation(self):
        words = [
            WordInfo("Hello,", 0.0, 0.5),
            WordInfo("world", 0.5, 1.0),
            WordInfo("this", 1.0, 1.5),
            WordInfo("is.", 1.5, 2.0),
            WordInfo("A", 2.0, 2.5),
            WordInfo("test?", 2.5, 3.0),
        ]
        chunks = self.node.group_words_into_chunks(words, max_words=4)

        # "Hello," has comma -> chunk 1: ["Hello,"]
        # "world", "this", "is." has dot -> chunk 2: ["world", "this", "is."]
        # "A", "test?" has question mark -> chunk 3: ["A", "test?"]

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0]["text"], "Hello,")
        self.assertEqual(chunks[1]["text"], "world this is.")
        self.assertEqual(chunks[2]["text"], "A test?")

    def test_group_words_into_chunks_max_words_1(self):
        words = [
            WordInfo("One", 0.0, 1.0),
            WordInfo("Two", 1.0, 2.0),
            WordInfo("Three", 2.0, 3.0),
        ]
        chunks = self.node.group_words_into_chunks(words, max_words=1)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0]["text"], "One")
        self.assertEqual(chunks[1]["text"], "Two")
        self.assertEqual(chunks[2]["text"], "Three")

    def test_group_words_into_chunks_empty(self):
        chunks = self.node.group_words_into_chunks([], max_words=4)
        self.assertEqual(chunks, [])

    def test_group_words_into_chunks_no_break_needed(self):
        words = [
            WordInfo("Short", 0.0, 1.0),
            WordInfo("phrase", 1.0, 2.0),
        ]
        chunks = self.node.group_words_into_chunks(words, max_words=4)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["text"], "Short phrase")
        self.assertEqual(chunks[0]["start"], 0.0)
        self.assertEqual(chunks[0]["end"], 2.0)

    def test_group_words_into_chunks_strips_whitespace(self):
        words = [
            WordInfo("  Hello  ", 0.0, 1.0),
            WordInfo("\nworld\t", 1.0, 2.0),
        ]
        chunks = self.node.group_words_into_chunks(words, max_words=4)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["text"], "Hello world")

    def test_format_time_ass_basic(self):
        self.assertEqual(self.node.format_time_ass(0.0), "0:00:00.00")
        self.assertEqual(self.node.format_time_ass(1.23), "0:00:01.23")
        self.assertEqual(self.node.format_time_ass(61.5), "0:01:01.50")
        self.assertEqual(self.node.format_time_ass(3661.0), "1:01:01.00")

    def test_format_time_ass_rounding(self):
        # 1.234 -> 1.23
        self.assertEqual(self.node.format_time_ass(1.234), "0:00:01.23")
        # 1.236 -> 1.24
        self.assertEqual(self.node.format_time_ass(1.236), "0:00:01.24")

    def test_format_time_ass_rollover_seconds(self):
        # 59.996 -> 1:00.00
        self.assertEqual(self.node.format_time_ass(59.996), "0:01:00.00")

    def test_format_time_ass_rollover_minutes(self):
        # 3599.996 -> 1:00:00.00
        self.assertEqual(self.node.format_time_ass(3599.996), "1:00:00.00")

    def test_translate_chunks_no_translation(self):
        chunks = [{"text": "Hello world"}]
        result = self.node.translate_chunks(chunks, "Original")
        self.assertEqual(result[0]["text"], "Hello world")
        self.assertNotIn("is_translated", result[0])

        result2 = self.node.translate_chunks(chunks, "English")
        self.assertEqual(result2[0]["text"], "Hello world")
        self.assertNotIn("is_translated", result2[0])

    @patch('captions_node.GoogleTranslator')
    def test_translate_chunks_success(self, MockTranslator):
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola mundo"
        MockTranslator.return_value = mock_translator_instance

        chunks = [{"text": "Hello world"}]
        result = self.node.translate_chunks(chunks, "Spanish")

        self.assertEqual(result[0]["text"], "Hola mundo")
        self.assertTrue(result[0]["is_translated"])
        MockTranslator.assert_called_once_with(source='auto', target='es')
        mock_translator_instance.translate.assert_called_once_with("Hello world")

    @patch('captions_node.GoogleTranslator')
    def test_translate_chunks_fallback(self, MockTranslator):
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.side_effect = Exception("API Error")
        MockTranslator.return_value = mock_translator_instance

        chunks = [{"text": "Hello world"}]
        # This should NOT raise an exception, it should be caught and logged
        result = self.node.translate_chunks(chunks, "Spanish")

        # Verify chunks remain unchanged
        self.assertEqual(result[0]["text"], "Hello world")
        self.assertNotIn("is_translated", result[0])
        MockTranslator.assert_called_once_with(source='auto', target='es')
        mock_translator_instance.translate.assert_called_once_with("Hello world")

if __name__ == '__main__':
    unittest.main()
