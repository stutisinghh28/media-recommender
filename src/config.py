import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

# Root directory of the project
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database configuration
DB_DIR = PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "recommender.db"

# Raw response cache directory
RAW_DATA_DIR = DB_DIR / "raw"

# Create directories if they don't exist
DB_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# TMDB API Keys / Tokens
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN", "")

# Incremental Ingestion Cache Settings
# Titles updated or ingested within this threshold (in days) are considered fresh
# and will not be re-fetched from the API.
CACHE_STALE_DAYS = int(os.getenv("CACHE_STALE_DAYS", 7))

# Force Mock Ingestion Mode (even if API key exists)
FORCE_MOCK = os.getenv("FORCE_MOCK", "False").lower() in ("true", "1", "yes")

# Determine if we should run in Mock mode
def is_mock_mode() -> bool:
    if FORCE_MOCK:
        return True
    # If no token/key is available, we run in mock mode
    return not (TMDB_API_KEY or TMDB_ACCESS_TOKEN)
