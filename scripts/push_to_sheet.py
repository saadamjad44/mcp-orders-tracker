"""Upload data/orders.csv into your Google Sheet (tab "Orders").

One-time setup (see README, "Google Sheets mode"):
  1. Create a service account, download its JSON key to data/creds.json
  2. Create an empty Google Sheet, share it with the service-account email as Editor
  3. Put the sheet id in .env as SHEET_ID

Usage:  python scripts/push_to_sheet.py

After uploading you can lower the service account to Viewer: the server only reads.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_path(name: str, default: str) -> Path:
    p = Path(os.getenv(name, default))
    return p if p.is_absolute() else BASE_DIR / p


def main() -> int:
    import gspread

    creds = env_path("GOOGLE_CREDS", "data/creds.json")
    csv_path = env_path("ORDERS_CSV", "data/orders.csv")
    sheet_id = os.getenv("SHEET_ID", "").strip()
    tab = os.getenv("WORKSHEET", "Orders").strip()

    if not sheet_id:
        print("SHEET_ID is empty in .env"); return 1
    if not creds.exists():
        print(f"Credentials file not found: {creds}"); return 1
    if not csv_path.exists():
        print(f"{csv_path} not found. Run scripts/generate_data.py first."); return 1

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    client = gspread.service_account(filename=str(creds))
    sheet = client.open_by_key(sheet_id)
    try:
        ws = sheet.worksheet(tab)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=tab, rows=len(rows) + 50, cols=len(rows[0]))
    ws.clear()
    # RAW keeps values exactly as typed, so phone numbers keep their leading zero.
    ws.update(range_name="A1", values=rows, value_input_option="RAW")
    ws.freeze(rows=1)
    print(f"Uploaded {len(rows) - 1} rows to tab '{tab}' of: {sheet.title}")
    print(f"Open it: https://docs.google.com/spreadsheets/d/{sheet_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
