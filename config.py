import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_CONFIG = PROJECT_DIR / "config.local.json"

try:
    with LOCAL_CONFIG.open(encoding="utf-8") as file:
        settings = json.load(file)
except FileNotFoundError:
    settings = {}

APP_TOKEN = settings.get("APP_TOKEN", "")
TABLE_ID = settings.get("TABLE_ID", "")
PERSONAL_BASE_TOKEN = settings.get("PERSONAL_BASE_TOKEN", "")
VIEW_ID = settings.get("VIEW_ID", "")
ATTACHMENT_FIELD_NAME = settings.get("ATTACHMENT_FIELD_NAME", "图片")

BASE_DIR = PROJECT_DIR / Path(settings.get("BASE_DIR", "data")).expanduser()
COVER_FOLDER_NAME = settings.get("COVER_FOLDER_NAME", "cover")
DETAIL_FOLDER_NAMES = settings.get("DETAIL_FOLDER_NAMES", ["detail-1", "detail-2", "detail-3"])

ENABLE_COMPRESSION = settings.get("ENABLE_COMPRESSION", True)
MAX_IMAGE_WIDTH = settings.get("MAX_IMAGE_WIDTH", 900)
OVERWRITE_EXISTING_ROWS = settings.get("OVERWRITE_EXISTING_ROWS", False)
START_ROW_NUMBER = settings.get("START_ROW_NUMBER", 1)
