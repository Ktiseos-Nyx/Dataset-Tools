"""
parameter_statistic_DB.py

This module provides database operations for the ExifData Analytics project.
It manages a SQLite database for storing and retrieving image metadata,
and offers various utility functions for database management and analysis.

Key features:
- Database connection and table creation
- Metadata insertion and retrieval
- Bulk operations for efficient data processing
- Database optimization and integrity checking
- Utility functions for database statistics and searches

Usage:
This module is typically imported and used by other scripts in the project.
It can also be run directly.
"""

import sqlite3
import os
import logging
import json
from typing import List, Tuple, Optional, Dict, Any, Generator
from pathlib import Path
import configparser
import time
from datetime import datetime

# Configuration and Logging Setup
config = configparser.ConfigParser()
script_dir = Path(__file__).resolve().parent
config_path = script_dir / 'config.ini'

try:
    config.read(config_path)
except configparser.Error as e:
    print(f"Error reading config file: {e}")
    exit(1)

logging_dir = script_dir / config['Paths']['logging_dir']
logging_dir.mkdir(exist_ok=True)

logger = logging.getLogger('db')
logger.setLevel(logging.DEBUG)

log_file_path = logging_dir / "process_logDB.txt"
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Database configuration
DB_NAME = config['Database']['db_name']
DB_PATH = script_dir / DB_NAME

# Constants
VALID_IMAGE_EXTENSIONS = ('.png', '.jpeg', '.jpg')

def db_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('PRAGMA synchronous = OFF')
        conn.execute('PRAGMA journal_mode = MEMORY')
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error occurred while connecting to the SQLite database: {e}")
        raise

def create_table() -> None:
    """Creates the file_metadata table if it doesn't exist."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    file_name TEXT UNIQUE,
                    file_path TEXT,
                    last_modified REAL,
                    metadata TEXT,
                    metadata_after_prompt TEXT,
                    PRIMARY KEY (file_name)
                );
            """)
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error occurred while creating table: {e}")
        raise

# Metadata Operations
def normalize_metadata(metadata: Optional[str]) -> Optional[str]:
    """Normalizes metadata by converting all keys to lowercase and trimming whitespace."""
    if metadata is None:
        return None
    normalized_lines = [f'{key.strip().lower()}: {value.strip()}' for line in metadata.split('\n') if ': ' in line for key, value in [line.split(': ', 1)]]
    return '\n'.join(normalized_lines)

def update_or_insert_metadata(file_name: str, file_path: str, metadata: str) -> None:
    """Updates or inserts metadata for a file."""
    if not file_name or not file_path or not metadata:
        raise ValueError("file_name, file_path, and metadata are required parameters")

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            parts = metadata.split("Negative prompt:", 1)
            metadata_before_prompt = normalize_metadata(parts[0].strip()) if parts else None
            metadata_after_prompt = normalize_metadata(parts[1].strip()) if len(parts) > 1 else ""

            if not Path(file_path).exists():
                raise FileNotFoundError(f"File '{file_path}' does not exist")
            last_modified = os.path.getmtime(file_path)

            cursor.execute("""
                INSERT INTO file_metadata (file_name, file_path, last_modified, metadata, metadata_after_prompt)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_name) 
                DO UPDATE SET 
                    file_path = EXCLUDED.file_path,
                    last_modified = EXCLUDED.last_modified, 
                    metadata = EXCLUDED.metadata,
                    metadata_after_prompt = EXCLUDED.metadata_after_prompt;
                """, (file_name, file_path, last_modified, metadata_before_prompt, metadata_after_prompt))
            conn.commit()
    except (sqlite3.Error, FileNotFoundError) as e:
        logger.error(f"Error in update_or_insert_metadata: {e}")
        raise

def bulk_update_or_insert_metadata(records: List[Tuple[str, str, str]]) -> None:
    """Updates or inserts metadata for multiple files in bulk."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            bulk_records = []
            for record in records:
                file_name, file_path, metadata = record
                parts = metadata.split("Negative prompt:", 1)
                metadata_before_prompt = normalize_metadata(parts[0].strip()) if parts else None
                metadata_after_prompt = normalize_metadata(parts[1].strip()) if len(parts) > 1 else ""

                if not Path(file_path).exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                last_modified = os.path.getmtime(file_path)
                
                bulk_records.append((file_name, file_path, last_modified, metadata_before_prompt, metadata_after_prompt))

            conn.executemany("""
                INSERT INTO file_metadata (file_name, file_path, last_modified, metadata, metadata_after_prompt)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_name) 
                DO UPDATE SET 
                    file_path = EXCLUDED.file_path,
                    last_modified = EXCLUDED.last_modified, 
                    metadata = EXCLUDED.metadata,
                    metadata_after_prompt = EXCLUDED.metadata_after_prompt;
                """, bulk_records)
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error in bulk_update_or_insert_metadata: {e}")
        raise

def get_metadata(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Retrieves metadata for a given file path from the database."""
    if not file_path:
        raise ValueError("file_path is a required parameter")

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata, metadata_after_prompt FROM file_metadata WHERE file_path = ?", (file_path,))
            data = cursor.fetchone()
        return data if data else (None, None)
    except sqlite3.Error as e:
        logger.error(f"Error in get_metadata: {e}")
        raise

def get_metadata_batch(batch_size: int = 1000) -> Generator[List[Tuple[str, str, str, str, str]], None, None]:
    """Retrieves metadata for multiple files in batches."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            offset = 0
            while True:
                cursor.execute("""
                    SELECT file_name, file_path, last_modified, metadata, metadata_after_prompt
                    FROM file_metadata
                    LIMIT ? OFFSET ?
                """, (batch_size, offset))
                batch = cursor.fetchall()
                if not batch:
                    break
                yield batch
                offset += batch_size
    except sqlite3.Error as e:
        logger.error(f"Error in get_metadata_batch: {e}")
        raise

# File and Path Operations
def is_file_updated(file_path: str) -> bool:
    """Checks if the file has been updated since the last check."""
    if not file_path:
        raise ValueError("file_path is a required parameter")
    
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_modified FROM file_metadata WHERE file_path = ?", (file_path,))
            data = cursor.fetchone()

            if not data:
                return True
            
            last_modified_db = data[0]
            last_modified_file = os.path.getmtime(file_path)
            
            return last_modified_file != last_modified_db
    except (sqlite3.Error, OSError) as e:
        logger.error(f"Error in is_file_updated: {e}")
        raise

def normalize_path(path: str) -> str:
    """Normalizes the file path to use a consistent separator."""
    return os.path.normpath(path)

# Model and Directory Operations
def list_models_in_directory(directory: str) -> Dict[str, List[str]]:
    """Lists models used for images within a specified directory."""
    models: Dict[str, List[str]] = {}

    if not directory:
        raise ValueError("directory is a required parameter")

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(VALID_IMAGE_EXTENSIONS):
                        file_path = os.path.join(root, file)
                        normalized_file_path = normalize_path(file_path)
                        cursor.execute("SELECT metadata_after_prompt FROM file_metadata WHERE file_path = ?", (normalized_file_path,))
                        data = cursor.fetchone()
                        
                        if data:
                            metadata_after_prompt = data[0]
                            model = extract_model_from_metadata(metadata_after_prompt)
                            
                            if model:
                                models.setdefault(model, []).append(normalized_file_path)
                        else:
                            logger.debug(f"No metadata found for file: {normalized_file_path}")
    except (sqlite3.Error, OSError) as e:
        logger.error(f"Error in list_models_in_directory: {e}")
        raise

    return models

def extract_model_from_metadata(metadata_after_prompt: str) -> Optional[str]:
    """Extracts the model name from metadata."""
    model = None

    for line in metadata_after_prompt.split(','):
        if "Model:" in line:
            model = line.split("Model:", 1)[1].strip()
            break
        elif "model:" in line:
            model = line.split("model:", 1)[1].strip()
            break
    
    if model is None:
        try:
            if "Civitai resources:" in metadata_after_prompt:
                json_string_start = metadata_after_prompt.index("Civitai resources:") + len("Civitai resources:")
                json_string = metadata_after_prompt[json_string_start:].strip()
                json_string = json_string.split(']', 1)[0] + ']'  
                json_data = json.loads(json_string)
                for item in json_data:
                    if 'modelName' in item:
                        model = item['modelName'].strip()
                        if model:
                            break
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to decode JSON in metadata: {e}")

    return model

# Database Management and Optimization
def optimize_database() -> None:
    """Optimizes the database by running VACUUM and ANALYZE."""
    try:
        with db_connection() as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
        logger.info("Database optimization completed successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error optimizing database: {e}")
        raise

def clear_database() -> None:
    """Clears all records from the file_metadata table."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_metadata")
            conn.commit()
            cursor.execute("VACUUM")  # Reclaim disk space
            conn.commit()
        logger.info("Database cleared successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error clearing database: {e}")
        raise

def backup_database(backup_dir: str) -> None:
    """Creates a backup of the database in the specified directory."""
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.splitext(os.path.basename(DB_PATH))[0]}_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        with db_connection() as conn:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
        logger.info(f"Database backup created at {backup_path}")
        print(f"Database backup created at {backup_path}")
    except sqlite3.Error as e:
        logger.error(f"Error creating database backup: {e}")
        print(f"Error creating database backup: {e}")
    except OSError as e:
        logger.error(f"Error creating backup directory: {e}")
        print(f"Error creating backup directory: {e}")

def check_database_integrity() -> bool:
    """Checks the integrity of the database."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            return result[0] == "ok"
    except sqlite3.Error as e:
        logger.error(f"Error checking database integrity: {e}")
        raise

# Database Statistics and Analysis
def get_database_stats() -> Dict[str, Any]:
    """Returns statistics about the database."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM file_metadata")
            total_records = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(length(metadata)) FROM file_metadata")
            avg_metadata_length = cursor.fetchone()[0]
        
        return {
            "total_records": total_records,
            "avg_metadata_length": avg_metadata_length
        }
    except sqlite3.Error as e:
        logger.error(f"Error getting database stats: {e}")
        raise

def get_database_size() -> int:
    """Returns the size of the database file in bytes."""
    try:
        return os.path.getsize(DB_PATH)
    except OSError as e:
        logger.error(f"Error getting database size: {e}")
        raise

def get_last_modified() -> float:
    """Returns the last modified timestamp of the database file."""
    try:
        return os.path.getmtime(DB_PATH)
    except OSError as e:
        logger.error(f"Error getting last modified time of database: {e}")
        raise


# Main Execution Block
if __name__ == "__main__":
    print("ExifData Analytics - Database Operations Module")
    print("===============================================")
    print("\nAvailable functions:")
    print("- database_stats + optimize_database" )
    print("- metadata_sample")
    print("- check_database_integrity")
    print("- backup_database")
    print("- database_size")
    print("- last_modified")
    print("- clear_database")
        
    choice = input("\nWould you like to run a quick database status check? (y/n): ").lower()
    if choice == 'y':
        try:
            create_table()
            stats = get_database_stats()
            print("\nDatabase Status:")
            print(f"Total records: {stats['total_records']}")
            print(f"Average metadata length: {stats['avg_metadata_length']:.2f} characters")
            
            print(f"\nDatabase size: {get_database_size() / (1024*1024):.2f} MB")
            print(f"Database last modified: {time.ctime(get_last_modified())}")
            
            optimize_database()
            print("\nDatabase optimization completed.")

        except Exception as e:
            print(f"An error occurred during the status check: {e}")    
           
    batch_choice = input("\nWould you like to see a sample of metadata batch processing? (y/n): ").lower()
    if batch_choice == 'y':
        batch_size = 10  # Small batch size for demonstration
        start_time = time.time()
        batch_generator = get_metadata_batch(batch_size)
        first_batch = next(batch_generator)
        print(f"\nProcessed first batch of {len(first_batch)} records in {time.time() - start_time:.4f} seconds.")
        print("Sample record:")
        print(f"File: {first_batch[0][0]}")
        print(f"Path: {first_batch[0][1]}")
        print(f"Last Modified: {first_batch[0][2]}")
        print(f"Metadata: {first_batch[0][3][:100]}...")  # Show first 100 characters of metadata
    
    integrity_choice = input("\nWould you like to perform a database integrity check? (y/n): ").lower()
    if integrity_choice == 'y':
        if check_database_integrity():
            print("Database integrity check passed.")
        else:
            print("Database integrity check failed. Please run a full check and consider restoring from a backup.")
        
        
    
    # Always continue to this point, regardless of the status check choice
    backup_choice = input("\nWould you like to create a database backup? (y/n): ").lower()
    if backup_choice == 'y':
        backup_dir = input("Enter the directory path for the backup: ").strip()
        try:
            backup_database(backup_dir)
        except Exception as e:
            print(f"An error occurred during the backup process: {e}")

    
    size_choice = input("\nWould you like to see the current database size? (y/n): ").lower()
    if size_choice == 'y':
        try:
            size_mb = get_database_size() / (1024 * 1024)
            print(f"Current database size: {size_mb:.2f} MB")
        except Exception as e:
            print(f"Error getting database size: {e}")

    last_modified_choice = input("\nWould you like to see when the database was last modified? (y/n): ").lower()
    if last_modified_choice == 'y':
        try:
            last_modified = get_last_modified()
            print(f"Database last modified: {time.ctime(last_modified)}")
        except Exception as e:
            print(f"Error getting last modified time: {e}")

    clear_database_prompt = input("\nWould you like to clear the database? (y/n): ").lower()
    if clear_database_prompt == 'y':
        confirm_clear = input("Are you absolutely sure you want to clear the database? This action cannot be undone. Type 'YES' to confirm: ").strip().upper()
        if confirm_clear == 'YES':
            try:
                clear_database()
                print("Database cleared successfully.")
            except Exception as e:
                print(f"Error clearing database: {e}")
        else:
            print("Database clear operation cancelled.")
    else:
        print("Database clear operation cancelled.")

    print("\nAll operations complete. Exiting.")
