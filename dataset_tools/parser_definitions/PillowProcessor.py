# PillowProcessor.py
from PIL import Image

from dataset_tools.logger import info_monitor


# Make sure to install Pillow: pip install Pillow
def inspect_png_chunks(filepath):
    with Image.open(filepath) as img:
        info_monitor("Inspecting metadata for: %s", filepath)
        if hasattr(img, "text") and img.text:
            for key, value in img.text.items():
                info_monitor("\n--- Found tEXt Chunk ---")
                info_monitor("Key: %s", key)
                info_monitor("Value: %r", value)  # Use repr() to see the full, raw string
                info_monitor("------------------------")
        else:
            info_monitor("No 'text' chunks found in the info dictionary.")


# Replace with the path to your image
# inspect_png_chunks("/Users/duskfall/Downloads/Metadata Samples/00004-2747468859.png")
