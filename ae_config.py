import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AE_BASE_URL = os.getenv("AE_BASE_URL", "").strip()
AE_ORG_CODE = os.getenv("AE_ORG_CODE", "").strip()
AE_USERNAME = os.getenv("AE_USERNAME", "").strip()
AE_PASSWORD = os.getenv("AE_PASSWORD", "").strip()
AE_SESSION_TOKEN = os.getenv("AE_SESSION_TOKEN", "").strip()

CACHE_FILE = "ae_mappings_cache.json"
CACHE_MAX_AGE_HOURS = 24
