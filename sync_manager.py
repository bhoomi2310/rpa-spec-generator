import json
import time
import threading
from datetime import datetime, timedelta
from ae_config import CACHE_FILE, CACHE_MAX_AGE_HOURS, AE_BASE_URL
from ae_client import (
    get_session_token,
    fetch_workflows,
    get_latest_update_timestamp
)

def load_cache() -> dict:
    """
    Reads the cached mappings.
    Returns default empty cache structure if file is missing or corrupt.
    """
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Validate basic cache structure
            if not isinstance(data, dict) or "mappings" not in data:
                return {"mappings": [], "last_synced": None, "last_server_ts": 0}
            return data
    except Exception:
        return {"mappings": [], "last_synced": None, "last_server_ts": 0}

def save_cache(mappings: list, server_ts: int):
    """
    Saves the mappings and synchronization timestamps to the cache file.
    """
    data = {
        "mappings": mappings,
        "last_synced": datetime.now().isoformat(),
        "last_server_ts": server_ts
    }
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save mappings to cache: {e}")

def is_cache_stale() -> bool:
    """
    Checks if the local cache is older than CACHE_MAX_AGE_HOURS.
    """
    cache = load_cache()
    last_synced = cache.get("last_synced")
    if not last_synced:
        return True
    try:
        dt = datetime.fromisoformat(last_synced)
        return (datetime.now() - dt) > timedelta(hours=CACHE_MAX_AGE_HOURS)
    except Exception:
        return True

def has_server_updated(session_token: str) -> bool:
    """
    Calls get_latest_update_timestamp() and compares with the last_server_ts in cache.
    Returns True if different.
    """
    server_ts = get_latest_update_timestamp(session_token)
    cache = load_cache()
    last_server_ts = cache.get("last_server_ts", 0)
    return server_ts != last_server_ts

def sync_mappings(force=False) -> list:
    """
    Attempts to sync workflows from AutomationEdge REST API.
    Falls back to cached workflows on configuration issues or network failure.
    """
    if not AE_BASE_URL:
        print("AutomationEdge not configured, loading from cache")
        return load_cache()["mappings"]

    try:
        token = get_session_token()
        server_ts = get_latest_update_timestamp(token)
        
        # Sync if forced, if cache has expired, or if server workflows changed
        if force or is_cache_stale() or has_server_updated(token):
            mappings = fetch_workflows(token)
            save_cache(mappings, server_ts)
            print(f"Synced {len(mappings)} workflows from AutomationEdge")
            return mappings
        else:
            print("Using cached mappings (up to date)")
            return load_cache()["mappings"]
    except Exception as error:
        print(f"AutomationEdge sync failed: {error} — using cached mappings")
        return load_cache()["mappings"]

def start_background_sync(callback=None):
    """
    Starts a background daemon thread that runs every 24 hours to sync workflows.
    If the sync returns a non-empty list of mappings, it invokes the optional callback.
    """
    def worker():
        while True:
            time.sleep(24 * 3600)
            try:
                mappings = sync_mappings(force=True)
                if callback and mappings:
                    callback(mappings)
            except Exception as e:
                print(f"Background sync error: {e}")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
