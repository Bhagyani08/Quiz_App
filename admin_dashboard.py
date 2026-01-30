#!/usr/bin/env python3
"""
Admin Dashboard - View all tracked quiz submissions from admin bin
"""

import requests
import json
from datetime import datetime

# JSONBin Configuration
JSONBIN_API_BASE = "https://api.jsonbin.io/v3"
ADMIN_BIN_ID = "6979e70643b1c97be951794c"

HEADERS = {
    "X-Master-Key": "$2a$10$0nEWKk89vS6CBYlIvV.zpuxU7Ja/DQ64Qk13e7mV60jM7ewVcYuGa",
    "Content-Type": "application/json"
}

def get_admin_data():
    """Retrieve admin bin data"""
    url = f"{JSONBIN_API_BASE}/b/{ADMIN_BIN_ID}/latest"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()["record"]
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error fetching admin bin: {e}")
        return None

def display_submissions():
    """Display all tracked submissions"""
    print("=" * 80)
    print("📊 Quiz Submissions Admin Dashboard")
    print("=" * 80)
    print()
    
    admin_data = get_admin_data()

    print(admin_data)
    
    if not admin_data:
        print("⚠️  Could not retrieve admin data")
        return
    
    submissions = admin_data.get("submissions", [])
    
    if not submissions:
        print("ℹ️  No submissions tracked yet")
        return
    
    print(f"Total Submissions: {len(submissions)}\n")
    print("-" * 80)
    
    # Sort by timestamp (newest first)
    submissions_sorted = sorted(submissions, key=lambda x: x.get("timestamp", 0), reverse=True)
    
    for idx, sub in enumerate(submissions_sorted, 1):
        bin_id = sub.get("bin_id", "Unknown")
        name = sub.get("name", "Unknown")
        email = sub.get("email", "Unknown")
        timestamp = sub.get("timestamp", 0)
        
        # Format timestamp
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = "Unknown"
        
        print(f"{idx}. {name}")
        print(f"   Email: {email}")
        print(f"   Bin ID: {bin_id}")
        print(f"   Submitted: {time_str}")
        print("-" * 80)
    
    # Save to JSON file for easy access
    output_file = "admin_submissions_list.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(submissions_sorted, f, indent=2)
    
    print(f"\n💾 Full list saved to: {output_file}")

def export_bin_ids():
    """Export just the bin IDs to a text file"""
    admin_data = get_admin_data()
    
    if not admin_data:
        return
    
    submissions = admin_data.get("submissions", [])
    bin_ids = [sub.get("bin_id") for sub in submissions if sub.get("bin_id")]
    
    output_file = "tracked_bin_ids.txt"
    with open(output_file, 'w') as f:
        for bin_id in bin_ids:
            f.write(f"{bin_id}\n")
    
    print(f"📋 Exported {len(bin_ids)} bin IDs to: {output_file}")

if __name__ == "__main__":
    display_submissions()
    print()
    export_bin_ids()
