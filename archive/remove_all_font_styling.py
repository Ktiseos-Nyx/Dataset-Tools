
import os


def remove_all_font_styling_from_qss(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".qss"):
                file_path = os.path.join(root, file)
                with open(file_path) as f:
                    lines = f.readlines()

                new_lines = []
                modified = False
                in_qfontcombobox_block = False

                for line in lines:
                    if "QFontComboBox" in line and "{" in line:
                        in_qfontcombobox_block = True
                        modified = True
                        continue # Skip the start of the block

                    if in_qfontcombobox_block:
                        if "}" in line:
                            in_qfontcombobox_block = False
                            modified = True
                        continue # Skip lines within the block

                    if "font-style" in line:
                        modified = True
                        continue # Skip font-style lines

                    new_lines.append(line)

                if modified:
                    print(f"Removing font-style and QFontComboBox styling from {file_path}")
                    with open(file_path, "w") as f:
                        f.writelines(new_lines)

if __name__ == "__main__":
    themes_directory = "dataset_tools/themes"
    remove_all_font_styling_from_qss(themes_directory)
