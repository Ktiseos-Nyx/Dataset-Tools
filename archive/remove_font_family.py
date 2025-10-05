
import os


def remove_font_family_from_qss(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".qss"):
                file_path = os.path.join(root, file)
                with open(file_path) as f:
                    lines = f.readlines()

                new_lines = [line for line in lines if "font-family" not in line]

                if len(new_lines) < len(lines):
                    print(f"Removing font-family from {file_path}")
                    with open(file_path, "w") as f:
                        f.writelines(new_lines)

if __name__ == "__main__":
    themes_directory = "dataset_tools/themes"
    remove_font_family_from_qss(themes_directory)
