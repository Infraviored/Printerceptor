import pathlib

# Directories
WATCH_DIR = pathlib.Path("claw").absolute()
OUTPUT_DIR = pathlib.Path("output_pdfs").absolute()
ARCHIVE_DIR = pathlib.Path("archive").absolute()
CUSTOMERS_FILE = pathlib.Path("customers.json").absolute()

def setup_directories():
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
