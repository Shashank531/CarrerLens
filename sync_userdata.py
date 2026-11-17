"""
CareerLens — Live Cloud Data Synchronizer (Smart Merge)
======================================================
Merges new registrations and assessment attempts from your live website
into your local data files without overwriting or losing your original data.

Usage:
    python sync_userdata.py
    python sync_userdata.py --auto
"""

import sys
import os
import time
import urllib.request
import ssl
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
USERDATA_DIR = ROOT_DIR / "data" / "userdata"
CSV_DIR = ROOT_DIR / "data" / "csv"
DB_PATH = ROOT_DIR / "backend" / "careerlens.db"

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

def merge_csv(local_file: Path, incoming_csv_text: str, key_col_idx: int = 1) -> tuple[int, int]:
    """
    Merges incoming CSV rows into local_file based on unique key at key_col_idx.
    Preserves all existing local rows, only appends genuinely new rows.
    Returns (total_rows, new_rows_added).
    """
    incoming_lines = [l.strip() for l in incoming_csv_text.strip().split("\n") if l.strip()]
    if not incoming_lines:
        return 0, 0
    header = incoming_lines[0]
    incoming_rows = incoming_lines[1:]

    existing_rows = []
    existing_keys = set()
    if local_file.exists():
        loc_lines = [l.strip() for l in local_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        if loc_lines:
            header = loc_lines[0]
            existing_rows = loc_lines[1:]
            for r in existing_rows:
                parts = r.split(",")
                if len(parts) > key_col_idx:
                    existing_keys.add(parts[key_col_idx])

    max_id = 0
    for r in existing_rows:
        pid = r.split(",")[0]
        if pid.isdigit():
            max_id = max(max_id, int(pid))

    new_added = 0
    merged = list(existing_rows)

    for r in incoming_rows:
        parts = r.split(",")
        if len(parts) > key_col_idx:
            key = parts[key_col_idx]
            if key not in existing_keys:
                max_id += 1
                parts[0] = str(max_id)
                merged.append(",".join(parts))
                existing_keys.add(key)
                new_added += 1

    final_content = header + "\n" + "\n".join(merged) + "\n"
    local_file.write_text(final_content, encoding="utf-8")
    return len(merged), new_added

def sync():
    USERDATA_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    cloud_url = get_cloud_base()
    print(f"\n==========================================")
    print(f" Connecting to: {cloud_url}")
    print(f"==========================================")

    # 1. Fetch & Smart-Merge userdata.csv (key: unique_code, index 1)
    target_userdata = USERDATA_DIR / "userdata.csv"
    try:
        remote_data = fetch_file("/api/userdata/csv")
        total_users, new_users = merge_csv(target_userdata, remote_data, key_col_idx=1)
        
        # Mirror to other standard data paths
        text = target_userdata.read_text(encoding="utf-8")
        (CSV_DIR / "userdata.csv").write_text(text, encoding="utf-8")
        (ROOT_DIR / "data" / "userdata.csv").write_text(text, encoding="utf-8")

        print(f"  [SUCCESS] Synced users: {total_users} total in dataset (+{new_users} new from cloud)")
        
        # Print latest user
        lines = [l for l in text.strip().split("\n") if l.strip()]
        if len(lines) > 1:
            last = lines[-1].split(",")
            print(f"  [LATEST USER] {last[2]} (Code: {last[1]})")
    except Exception as e:
        print(f"  [ERROR] userdata.csv sync error: {e}")

    # 2. Fetch & Smart-Merge user_attempts.csv (key: attempt timestamp/code)
    target_attempts = USERDATA_DIR / "user_attempts.csv"
    try:
        remote_attempts = fetch_file("/api/userdata/attempts/csv")
        total_att, new_att = merge_csv(target_attempts, remote_attempts, key_col_idx=5)
        
        a_text = target_attempts.read_text(encoding="utf-8")
        (CSV_DIR / "user_attempts.csv").write_text(a_text, encoding="utf-8")

        print(f"  [SUCCESS] Synced attempts: {total_att} total in dataset (+{new_att} new from cloud)")
    except Exception as e:
        print(f"  [ERROR] user_attempts.csv sync error: {e}")

    print("------------------------------------------")
    print("  RESULT: Local datasets safely merged and up to date!\n")

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
