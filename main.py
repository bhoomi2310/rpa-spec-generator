"""
RPA Workflow Spec Generator
============================
Entry point — launches the desktop GUI with background synchronization.
"""

from sync_manager import sync_mappings, start_background_sync
import catalog_client
from gui import launch_gui

if __name__ == "__main__":
    # Startup sequence
    print("Starting RPA Spec Generator...")
    print("Authenticating with AutomationEdge via OAuth2...")
    
    # Run initial sync
    mappings = sync_mappings()
    catalog_client.initialize(mappings)
    
    print(f"Ready — {len(mappings)} workflows loaded")
    
    # Launch GUI and supply callback to start background sync daemon after GUI start
    launch_gui(on_start=lambda: start_background_sync(callback=catalog_client.initialize))
