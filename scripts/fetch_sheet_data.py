#!/usr/bin/env python3
"""Pulls live data from the Apes Hill Villas Master Commissioning Tracker
Google Sheet and writes data/villas_extract.json + data/villa_issues.json
in the exact shape generate_villas.py expects.

Auth: a Google Cloud service account with read-only access to the Sheet
(see README.md "Step 2"). Needs two environment variables, both provided as
GitHub Actions secrets in the real workflow:

    GOOGLE_SERVICE_ACCOUNT_JSON  -- the full service-account key, as JSON text
    GOOGLE_SHEET_ID              -- the Sheet's id (the long string in its URL,
                                    between /d/ and /edit)

NOTE ON CALIBRATION: the per-villa row ranges below (checklist, keypads,
closeout, module outputs, lamp dimmers, module registry) are carried over
from the one-off extraction already verified against this sheet, and match
known-good row counts for every villa checked so far (23/26/8/48/11/12).
The header metadata block (technician, processor model, etc.) and the
Issues & Changes tab are read by SEARCHING for their label text rather than
a fixed cell address, so a reordered column shouldn't break them -- but
this script has not yet run against a live service account (that needs
Step 2 of README.md, which only Jeevan can complete). Treat the first real
run as a calibration pass: compare its output to data/villas_extract.json
and data/villa_issues.json already in this repo, which are known-correct.
"""
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

VILLAS = ["Villa 2", "Villa 4", "Villa 5", "Villa 6", "Villa 7"]
ISSUES_TAB = "Issues & Changes"  # confirm this is the live tab's real name

# 1-indexed row ranges, verified against every villa tab checked so far.
ROW_RANGES = {
    "checklist": (19, 41, "A:E"),
    "keypads": (46, 71, "A:G"),
    "closeout": (76, 83, "A:D"),
    "mods_out": (88, 135, "A:H"),
    "lamps": (139, 149, "A:G"),
    "modreg": (156, 167, "A:F"),
}

HEADER_LABELS = {
    "overall_status": "Overall Status",
    "base_template": "Base Template",
    "technician": "Technician",
    "date_worked": "Date Worked",
    "processor_model": "Processor Model",
    "processor_serial": "Processor Serial",
    "firmware": "Firmware",
    "mac": "MAC",
    "network": "Network",
    "project_file": "Project File",
    "factory_reset_date": "Factory Reset Date",
    "backup_location": "Backup Location",
}


def get_service():
    key_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def read_range(service, sheet_id, tab, a1_range):
    resp = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"'{tab}'!{a1_range}"
    ).execute()
    return resp.get("values", [])


def pad(row, width):
    row = list(row) + [""] * (width - len(row))
    return [c if c is not None else "" for c in row[:width]]


def parse_header_block(rows):
    """rows: the top ~18 rows of a villa tab. Find each HEADER_LABELS entry
    by searching for its label text anywhere in the row, taking the next
    non-empty cell on that row as the value."""
    out = {k: "" for k in HEADER_LABELS}
    out["sheet_name"] = ""
    out["header_a1"] = rows[0][0] if rows and rows[0] else ""
    for row in rows:
        for i, cell in enumerate(row):
            if not cell:
                continue
            for field, label in HEADER_LABELS.items():
                if cell.strip().lower() == label.lower():
                    value = next((c for c in row[i + 1:] if c), "")
                    out[field] = value
    return out


def extract_table(service, sheet_id, tab, key):
    start, end, cols = ROW_RANGES[key]
    width = {"A:E": 5, "A:G": 7, "A:D": 4, "A:H": 8, "A:F": 6}[cols]
    rows = read_range(service, sheet_id, tab, f"{cols}{start}:{cols[-1]}{end}")
    return [pad(r, width) for r in rows]


def extract_villa(service, sheet_id, villa):
    header_rows = read_range(service, sheet_id, villa, "A1:H18")
    header = parse_header_block(header_rows)
    header["sheet_name"] = villa

    kp_act_row = extract_table(service, sheet_id, villa, "keypads")
    notes_rows = read_range(service, sheet_id, villa, "A170:A220")
    notes = "\n".join(r[0] for r in notes_rows if r and r[0])

    header.update({
        "notes": notes,
        "kp_act": sum(1 for r in kp_act_row if r[4] == "Pass"),
        "kp_act_den": f"/ {len(kp_act_row)}",
        "kp_test": sum(1 for r in kp_act_row if r[5] == "Pass"),
        "kp_test_den": f"/ {len(kp_act_row)}",
        "checklist": extract_table(service, sheet_id, villa, "checklist"),
        "keypads": kp_act_row,
        "closeout": extract_table(service, sheet_id, villa, "closeout"),
        "mods_out": extract_table(service, sheet_id, villa, "mods_out"),
        "lamps": extract_table(service, sheet_id, villa, "lamps"),
        "modreg": extract_table(service, sheet_id, villa, "modreg"),
    })
    checklist = header["checklist"]
    header["tasks_pass"] = sum(1 for r in checklist if r[1] == "Pass")
    header["tasks_den"] = f"/ {len(checklist)}"
    header["open_defects"] = sum(1 for r in header["mods_out"] if r[6] == "Fail")
    modreg = header["modreg"]
    header["dim_mod"] = sum(1 for r in modreg if "dim" in r[1].lower())
    header["dim_mod_den"] = f"/ {header['dim_mod']}"
    header["sw_mod"] = sum(1 for r in modreg if "switch" in r[1].lower() or "sw" in r[1].lower())
    header["sw_mod_den"] = f"/ {header['sw_mod']}"
    return header


def extract_issues(service, sheet_id):
    rows = read_range(service, sheet_id, ISSUES_TAB, "A1:L500")
    if not rows:
        return {}
    header_row = rows[0]
    by_villa = {}
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        row = pad(row, 12)
        villa = row[1]
        by_villa.setdefault(villa, []).append(row)
    return by_villa


def fetch():
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    service = get_service()

    extract = {}
    for villa in VILLAS:
        print("fetching", villa)
        extract[villa] = extract_villa(service, sheet_id, villa)

    print("fetching", ISSUES_TAB)
    issues = extract_issues(service, sheet_id)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(extract, open(DATA_DIR / "villas_extract.json", "w"), indent=2)
    json.dump(issues, open(DATA_DIR / "villa_issues.json", "w"), indent=2)
    print("wrote data/villas_extract.json and data/villa_issues.json")


def main():
    # A live-fetch failure (the Sheets API not yet enabled, a transient
    # Google API error, a sheet layout this script hasn't been calibrated
    # against yet) should never block regenerating and republishing the
    # site from whatever is already committed in data/. Fail loudly in the
    # logs, but exit 0 so the rest of the Update Site workflow still runs.
    try:
        fetch()
    except Exception as exc:
        print(f"::warning::Live Sheet fetch failed, rebuilding from the data already committed in data/: {exc}")


if __name__ == "__main__":
    main()
