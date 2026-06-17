import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AE_BASE_URL = os.getenv("AE_BASE_URL", "https://t4.automationedge.com").strip()
AE_ORG_CODE = os.getenv("AE_ORG_CODE", "GENPACT_COPILOT").strip()
AE_CLIENT_ID = os.getenv("AE_CLIENT_ID", "").strip()
AE_CLIENT_SECRET = os.getenv("AE_CLIENT_SECRET", "").strip()

CACHE_FILE = "ae_mappings_cache.json"
CACHE_MAX_AGE_HOURS = 24
