"""
DB_filler.py

This script extracts EXIF metadata from images and populates a SQLite database.
It's part of the ExifData Analytics project for analyzing AI-generated image metadata.

Usage: python DB_filler.py
"""

import os
import subprocess
import sys
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import configparser
from pathlib import Path
import parameter_statistic_DB as db_module

# Check Python version
if sys.version_info < (3, 7):
    print("This script requires Python 3.7 or higher.")
    sys.exit(1)

# Get the directory of the current script
script_dir = Path(__file__).resolve().parent

# Load configuration
config = configparser.ConfigParser()
config_path = script_dir / 'config.ini'
try:
    config.read(config_path)
except configparser.Error as e:
    print(f"Error reading config file: {e}")
    sys.exit(1)

if not config_path.exists():
    print(f"Config file not found: {config_path}")
    sys.exit(1)

# Validate required config sections and options
required_sections = ['Paths', 'Processing', 'Database']
required_options = {
    'Paths': ['logging_dir'],
    'Processing': ['batch_size', 'max_workers'],
    'Database': ['db_name']
}

for section in required_sections:
    if section not in config:
        print(f"Missing required section in config: {section}")
        sys.exit(1)
    for option in required_options[section]:
        if option not in config[section]:
            print(f"Missing required option in config: [{section}] {option}")
            sys.exit(1)


# Setup logging
logging_dir = script_dir / config['Paths']['logging_dir']
logging_dir.mkdir(exist_ok=True)

logger = logging.getLogger('DB_filler')
logger.setLevel(logging.DEBUG)

log_file_path = logging_dir / "DB_filler_LOG.txt"
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Constants
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
BATCH_SIZE = int(config['Processing']['batch_size'])
MAX_WORKERS = int(config['Processing']['max_workers'])

def check_exiftool() -> Tuple[Optional[str], Optional[str]]:
    """Checks if ExifTool is installed and returns its command."""
    try:
        exiftool_cmd = "exiftool.exe" if sys.platform.startswith('win32') else "exiftool"
        subprocess.run([exiftool_cmd, "-ver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return exiftool_cmd, None
    except FileNotFoundError:
        return None, "ExifTool not found. Please install it to use this script. https://exiftool.org/install.html"
    except subprocess.CalledProcessError:
        return None, "Error occurred while checking ExifTool."

def validate_directory(source_directory: str, include_subfolders: bool = False) -> Tuple[Optional[List[str]], Optional[str]]:
    """Validates that the specified directory exists and contains only image files with valid extensions."""
    try:
        source_path = Path(source_directory)
        if not source_path.is_dir():
            return None, f"'{source_directory}' does not exist or is not a valid directory."

        if include_subfolders:
            image_files = [str(f) for f in source_path.rglob('*') if f.suffix.lower() in VALID_EXTENSIONS]
        else:
            image_files = [str(f) for f in source_path.iterdir() if f.suffix.lower() in VALID_EXTENSIONS]

        return image_files, None
    except PermissionError:
        return None, f"Permission denied to access '{source_directory}'."

def fetch_metadata(filepath: str, exiftool_cmd: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Fetch metadata for a single image file using ExifTool."""
    try:
        result = subprocess.run([exiftool_cmd, filepath], capture_output=True, text=True, check=True)
        return filepath, result.stdout, None
    except subprocess.CalledProcessError as e:
        return filepath, None, f"Error processing file: {e}"
    except Exception as e:
        return filepath, None, f"Unexpected error: {e}"

def update_database_with_images(image_files: List[str], exiftool_cmd: str) -> None:
    """Updates the database with metadata from the specified image files."""

    db_module.create_table()  # Ensure the table exists before updating the database

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_metadata, filepath, exiftool_cmd) for filepath in image_files]
        
        results = []
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing images", unit="file"):
            filepath, metadata, error = future.result()
            if error:
                logger.error(f"Error processing file {filepath}: {error}")
            else:
                results.append((Path(filepath).name, filepath, metadata))

            # Batch insert into the database
            if len(results) >= BATCH_SIZE:
                db_module.bulk_update_or_insert_metadata(results)
                results.clear()

        # Insert any remaining results
        if results:
            db_module.bulk_update_or_insert_metadata(results)

    logger.info("Finished adding Metadata from Images to the database.")

def main() -> None:
    """Main function to run the DB_filler script."""
    
    exiftool_cmd, error_message = check_exiftool()
    if error_message:
        logger.error(error_message)
        print(error_message)
        sys.exit(1)

    source_directory = input("Enter the directory to update the database with: ").strip()
    include_subfolders = input("Include subfolders? (yes/no): ").strip().lower() == 'yes'
    
    image_files, error_message = validate_directory(source_directory, include_subfolders)
    if error_message:
        logger.error(error_message)
        print(error_message)
        sys.exit(1)

    if not image_files:
        logger.warning("No valid image files found in the specified directory.")
        print("No valid image files found in the specified directory.")
        sys.exit(0)

    update_database_with_images(image_files, exiftool_cmd)
    print("Database update completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception("An unexpected error occurred:")
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)