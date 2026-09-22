# ============================================
# Configuration Settings for Influencer Finder
# ============================================

import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Browser Settings
HEADLESS = os.getenv("HEADLESS", "false").lower() in {"1", "true", "yes"}
TIMEOUT = 30  # Page load timeout (seconds)
BROWSER_DELAY = 2  # Delay between actions (seconds)

# File Paths
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(PROJECT_ROOT, "output"))
INSTAGRAM_SESSION_FILE = os.getenv(
    "INSTAGRAM_SESSION_FILE",
    os.path.join(PROJECT_ROOT, "instagram_session.json"),
)

# CSV Columns (bio NOT included in output — saves time)
CSV_COLUMNS = ["username", "profile_url", "niche", "score", "date_collected"]

print("Config loaded")
