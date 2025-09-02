# PillowProcessor.py
from PIL import Image


# Make sure to install Pillow: pip install Pillow
def inspect_png_chunks(filepath):
    with Image.open(filepath) as img:
        print(f"Inspecting metadata for: {filepath}")
        if hasattr(img, "text") and img.text:
            for key, value in img.text.items():
                print("\n--- Found tEXt Chunk ---")
                print(f"Key: {key}")
                print(f"Value: {value!r}") # Use repr() to see the full, raw string
                print("------------------------")
        else:
            print("No 'text' chunks found in the info dictionary.")

# Replace with the path to your image
inspect_png_chunks("/Users/duskfall/Downloads/Metadata Samples/00004-2747468859.png")
