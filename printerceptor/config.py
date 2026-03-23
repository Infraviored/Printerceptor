import pathlib
import json

# Internal Paths
WATCH_DIR = pathlib.Path("claw").absolute()
OUTPUT_DIR = pathlib.Path("output_pdfs").absolute()
ARCHIVE_DIR = pathlib.Path("archive").absolute()
CUSTOMERS_FILE = pathlib.Path("customers.json").absolute()
USER_CONFIG_FILE = pathlib.Path("config.json").absolute()

def load_user_config():
    """
    Load user-defined settings from the root config.json.
    """
    default_config = {
        "supported_formats": [".txt"],
        "archive_original": True,
        "fuzzy_threshold": 30
    }
    
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                default_config.update(user_data)
        except Exception as e:
            print(f"Error loading config.json: {e}. Using defaults.")
            
    return default_config

def setup_directories():
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
