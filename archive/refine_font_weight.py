
import os
import re


def refine_font_weight_in_qss(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".qss"):
                file_path = os.path.join(root, file)
                with open(file_path) as f:
                    content = f.read()

                # This is a simplified QSS parser. It might not handle all edge cases.
                # It works by splitting the content into blocks of rules.
                # Each rule is a selector and a block of properties in curly braces.

                new_content = ""
                # Use a regex to find all rules
                rules = re.findall(r"([^{}]+)({[^{}]+})", content)

                modified = False
                for selector, properties in rules:
                    selector = selector.strip()
                    properties = properties.strip()

                    if "QPushButton" not in selector:
                        # Remove font-weight from the properties
                        new_properties, count = re.subn(r"font-weight\s*:[^;]+;", "", properties)
                        if count > 0:
                            modified = True
                            properties = new_properties

                    new_content += selector + " " + properties + "\n"

                if modified:
                    print(f"Refining font-weight in {file_path}")
                    with open(file_path, "w") as f:
                        f.write(new_content)

if __name__ == "__main__":
    themes_directory = "dataset_tools/themes"
    refine_font_weight_in_qss(themes_directory)
