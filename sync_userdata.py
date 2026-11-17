"""
CareerLens — Live Cloud Data Synchronizer (sync_userdata.py)
============================================================
Pulls the latest user registrations, assessment attempts, and recommendations
from your live cloud website directly into your local data/ folder.

Usage:
    python sync_userdata.py
    python sync_userdata.py https://your-actual-url.onrender.com
    python sync_userdata.py --auto
"""

import sys
import os
import time
import urllib.request
import ssl
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
USERDATA_DIR = ROOT_DIR / "data" / "userdata"
CSV_DIR = ROOT_DIR / "data" / "csv"

DEFAULT_CLOUD_URL = "https://carrerlens-a3dl.onrender.com"

def get_cloud_base():
    for arg in sys.argv[1:]:
        if arg.startswith("http://") or arg.startswith("https://"):
            return arg.rstrip("/")
    return os.environ.get("CAREERLENS_CLOUD_URL", DEFAULT_CLOUD_URL).rstrip("/")

def fetch_file(endpoint: str) -> str:
    base = get_cloud_base()
    url = f"{base}{endpoint}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CareerLens-Sync/1.0"}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return resp.read().decode("utf-8")

def sync():
    USERDATA_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    cloud_url = get_cloud_base()
    print(f"\n==========================================")
    print(f" Connecting to: {cloud_url}")
    print(f"==========================================")

    success_users = False
    success_attempts = False

    # 1. Fetch userdata.csv
    try:
        userdata_content = fetch_file("/api/userdata/csv")
        target_userdata_files = [
            USERDATA_DIR / "userdata.csv",
            CSV_DIR / "userdata.csv",
            ROOT_DIR / "data" / "userdata.csv",
        ]
        for f in target_userdata_files:
            f.write_text(userdata_content, encoding="utf-8")
        
        lines = [l for l in userdata_content.strip().split("\n") if l.strip()]
        user_count = max(0, len(lines) - 1)
        print(f"  [SUCCESS] Synced userdata.csv ({user_count} total registered users)")
        if len(lines) > 1:
            last_cols = lines[-1].split(",")
            print(f"  [LATEST USER] {last_cols[2]} (Code: {last_cols[1]})")
        success_users = True
    except Exception as e:
        print(f"  [ERROR] Could not fetch userdata.csv from cloud server:")
        print(f"          -> {e}")

    # 2. Fetch user_attempts.csv
    try:
        attempts_content = fetch_file("/api/userdata/attempts/csv")
        target_attempt_files = [
            USERDATA_DIR / "user_attempts.csv",
            CSV_DIR / "user_attempts.csv",
        ]
        for f in target_attempt_files:
            f.write_text(attempts_content, encoding="utf-8")
        
        a_lines = [l for l in attempts_content.strip().split("\n") if l.strip()]
        attempt_count = max(0, len(a_lines) - 1)
        print(f"  [SUCCESS] Synced user_attempts.csv ({attempt_count} total test attempts)")
        success_attempts = True
    except Exception as e:
        print(f"  [ERROR] Could not fetch user_attempts.csv from cloud server:")
        print(f"          -> {e}")

    print("------------------------------------------")
    if success_users or success_attempts:
        print("  RESULT: Local data files successfully updated!\n")
    else:
        print("  RESULT: FAILED to update local files.")
        print("  Reason: The server at " + cloud_url + " returned an error.")
        print("  Please verify your Render service is Live and check the URL.\n")

if __name__ == "__main__":
    if "--auto" in sys.argv:
        print("Starting Auto-Sync daemon (Ctrl+C to stop)...")
        while True:
            try:
                sync()
            except Exception as ex:
                print(f"[Warning] Sync failed: {ex}")
            time.sleep(60)
    else:
        sync()
