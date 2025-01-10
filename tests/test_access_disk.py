import unittest
import os

from dataset_tools.access_disk import FileReader

class TestDiskInterface(unittest.TestCase):

    def setUp(self):
        self.reader = FileReader()
        self.test_folder = os.path.dirname(os.path.abspath(__file__))
        self.real_file = os.path.join(self.test_folder, "test_img.png")

    def test_read_png_header_fail(self):
        with self.assertRaises(FileNotFoundError):
            self.reader.read_header(os.path.join(self.test_folder, "nonexistent.png"))

    def test_read_png_header_succeed(self):
        """Do eeet"""
        chunks = self.reader.read_header(self.real_file)
        self.assertIsNotNone(chunks)
        self.assertTrue(list(chunks))  # Confirm it's not empty

if __name__ == "__main__":
    unittest.main()
