"""
CareerLens — Frontend Static Assets & HTML Reference Auditor
"""

import os
import re
from pathlib import Path

frontend_dir = Path("frontend")
html_files = sorted(list(frontend_dir.glob("*.html")))

print("=" * 65)
print("  Frontend HTML, Asset & Script Reference Integrity Audit")
print("=" * 65)

errors = []

for hf in html_files:
    print(f"\n[Auditing {hf.name}]")
    content = hf.read_text(encoding="utf-8")
    
    # 1. Script sources
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
    for s in scripts:
        if s.startswith("http://") or s.startswith("https://"):
            print(f"  CDN Script   : {s}")
        else:
            asset_path = frontend_dir / s
            if asset_path.exists():
                print(f"  Local Script : {s} ({asset_path.stat().st_size} bytes) [OK]")
            else:
                err = f"Missing script in {hf.name}: {s}"
                print(f"  [ERROR] {err}")
                errors.append(err)

    # 2. Image sources
    images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    for img in images:
        if img.startswith("data:") or img.startswith("http"):
            continue
        asset_path = frontend_dir / img
        if asset_path.exists():
            print(f"  Local Image  : {img} ({asset_path.stat().st_size} bytes) [OK]")
        else:
            err = f"Missing image in {hf.name}: {img}"
            print(f"  [ERROR] {err}")
            errors.append(err)

    # 3. CSS stylesheet links
    styles = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', content)
    for st in styles:
        if st.startswith("http://") or st.startswith("https://") or "fonts" in st:
            print(f"  CDN Font/CSS : {st}")
        else:
            asset_path = frontend_dir / st
            if asset_path.exists():
                print(f"  Local CSS    : {st} ({asset_path.stat().st_size} bytes) [OK]")
            else:
                err = f"Missing CSS in {hf.name}: {st}"
                print(f"  [ERROR] {err}")
                errors.append(err)

print("\n" + "=" * 65)
if not errors:
    print("  FRONTEND AUDIT COMPLETE: 0 BROKEN REFERENCES. ALL ASSETS EXIST!")
else:
    print(f"  AUDIT FINISHED WITH {len(errors)} ERRORS:")
    for e in errors:
        print("   -", e)
print("=" * 65)
