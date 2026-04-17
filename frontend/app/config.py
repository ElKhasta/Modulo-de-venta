from pathlib import Path
import os

from dotenv import load_dotenv


FRONTEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = FRONTEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
APP_TITLE = "Vantti POS"
