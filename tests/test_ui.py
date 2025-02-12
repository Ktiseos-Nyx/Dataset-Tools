# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Test UI"""

# import unittest
# from unittest.mock import MagicMock
# from dataset_tools.correct_types import UpField
# from dataset_tools.ui import MainWindow


# class TestDisplayText(unittest.TestCase):
#     """test class"""

# @patch("dataset_tools.ui.MainWindow.unpack_content_of")
# def test_display_text(self, mock_unpack):
# """test"""
# instance = MainWindow()

# # Mock widgets setters
# instance.top_separator, instance.mid_separator, instance.upper_box, instance.lower_box = [MagicMock()] * 4

# metadata = {"label": "data"}

# mock_unpack.side_effect = [{"title": "Up", "display": "Upper"}, {"title": "Mid", "display": "Lower"}]

# instance.display_text_of(metadata)

# instance.top_separator.setText.assert_called_with("Up")
# instance.upper_box.setText.assert_called_with("Upper")
# instance.mid_separator.setText.assert_called_with("Mid")
# instance.lower_box.setText.assert_called_with("Lower")

# def test_none_metadata(self):
#     """test"""
#     instance = MainWindow()

#     # Mock with placeholder
#     instance.top_separator, instance.mid_separator, instance.upper_box, instance.lower_box = [MagicMock()] * 4

#     instance.display_text_of(None)

#     placeholder = UpField.PLACEHOLDER
#     calls = [unittest.mock.call(placeholder)] * 4

#     self.assertEqual(instance.top_separator.setText.call_args_list, calls)


# if __name__ == "__main__":
#     unittest.main()
