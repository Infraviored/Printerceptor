import pathlib
import json

# Base Data Directory
DATA_DIR = pathlib.Path("data").absolute()

# Internal Paths - All moved into the 'data' folder
BON_INPUT_DIR = DATA_DIR / "bon_input"
RECHNUNG_OUTPUT_DIR = DATA_DIR / "rechnung_output"
ARCHIVE_DIR = DATA_DIR / "archive"
CUSTOMERS_FILE = pathlib.Path("customers.json").absolute()
USER_CONFIG_FILE = pathlib.Path("config") / "config.json"

def load_user_config():
    """
    Load user-defined settings from the config/config.json.
    """
    default_config = {
        "supported_formats": [".txt", ".pdf"],
        "archive_original": True,
        "fuzzy_threshold": 30,
        "auto_print_bon": True
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BON_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    RECHNUNG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
