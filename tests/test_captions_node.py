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

if __name__ == '__main__':
    unittest.main()
