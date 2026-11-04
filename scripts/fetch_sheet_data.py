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

Calibrated against the live sheet on 2026-11-03: row ranges, the header
metadata block's label text (rows 1-14 of each villa tab), the checklist
table's non-contiguous columns (A=item, C=status, D=evidence, F=date,
H=issue -- B/E/G are a merged blank and a per-row technician column this
pipeline doesn't use), and the notes cell (row 15, found by label text
rather than a fixed row) were all verified cell-by-cell against Villa 2,
4 and 6. Keypads, closeout, module outputs, lamp dimmers and the module
registry are contiguous ranges and matched on the first real run with no
changes needed.
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

# Each villa tab's metadata block (rows 1-14) pairs a label with its value
# on the SAME row. Simple fields take the next non-empty cell after the
# label; progress fields (a count plus a "/ N" denominator) take the next
# TWO non-empty cells. Label text confirmed verbatim against the live sheet.
SIMPLE_LABELS = {
    "overall_status": "Overall status",
    "base_template": "Base template",
    "technician": "Technician",
    "date_worked": "Date worked",
    "processor_model": "Processor model",
    "processor_serial": "Processor Serial Number",
    "firmware": "Firmware",
    "mac": "Processor MAC Address",
    "network": "Network IP / settings",
    "project_file": "Project file",
    "factory_reset_date": "Factory reset date",
    "backup_location": "Final backup location",
    "open_defects": "Open defects",
}
PROGRESS_LABELS = {
    ("kp_act", "kp_act_den"): "Keypads activated",
    ("kp_test", "kp_test_den"): "Keypads tested",
    ("tasks_pass", "tasks_den"): "Tasks passed",
    ("dim_mod", "dim_mod_den"): "Dimming modules activated",
    ("sw_mod", "sw_mod_den"): "Switching modules activated",
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
    """rows: A1:H14 of a villa tab -- stops before the checklist table's own
    header row (row 18), which also has cells literally labeled "Technician"
    and "Issue ID" that would otherwise collide with these same searches.
    Each label is matched by exact text (case-insensitive) anywhere in a
    row; simple fields take the next non-empty cell on that row, progress
    fields take the next two (the count, then its "/ N" denominator)."""
    out = {k: "" for k in SIMPLE_LABELS}
    for keys in PROGRESS_LABELS:
        out[keys[0]] = ""
        out[keys[1]] = ""
    for row in rows:
        for i, cell in enumerate(row):
            if not cell:
                continue
            label_text = cell.strip().lower()
            for field, label in SIMPLE_LABELS.items():
                if label_text == label.lower():
                    # The adjacent cell only -- NOT the next non-empty cell
                    # further along the row, which for a genuinely blank
                    # value (e.g. an unrecorded technician) would otherwise
                    # grab the next field's own label text from this same
                    # row instead of correctly staying blank.
                    out[field] = row[i + 1] if i + 1 < len(row) else ""
            for (val_field, den_field), label in PROGRESS_LABELS.items():
                if label_text == label.lower():
                    out[val_field] = row[i + 1] if i + 1 < len(row) else ""
                    out[den_field] = row[i + 2] if i + 2 < len(row) else ""
    return out


def extract_table(service, sheet_id, tab, key):
    start, end, cols = ROW_RANGES[key]
    first_col, last_col = cols.split(":")
    width = {"A:E": 5, "A:G": 7, "A:D": 4, "A:H": 8, "A:F": 6}[cols]
    rows = read_range(service, sheet_id, tab, f"{first_col}{start}:{last_col}{end}")
    return [pad(r, width) for r in rows]


# The checklist's "Status" column was a dropdown (Pass / Pending / Not
# Recorded) when this pipeline was calibrated; it's since become a plain
# checkbox, so the Sheets API now returns "TRUE"/"FALSE" there instead.
# Map those back to the vocabulary render_checklist()'s badge() already
# knows how to color -- ticked maps to Pass, unticked to Not Recorded
# (a checkbox can't distinguish "in progress" from "not looked at yet",
# so there's no equivalent for the old "Pending" state).
CHECKLIST_STATUS_MAP = {"TRUE": "Pass", "FALSE": "Not Recorded"}


def extract_checklist(service, sheet_id, tab):
    """The checklist table's columns aren't contiguous: A=item, B=(merged
    blank), C=status, D=evidence, E=(merged blank), F=date, G=technician
    (not needed here), H=issue id. Read the full width and pick out the
    five columns render_checklist() expects: item, status, evidence, date,
    issue."""
    start, end, _ = ROW_RANGES["checklist"]
    rows = read_range(service, sheet_id, tab, f"A{start}:H{end}")
    out = []
    for r in rows:
        r = pad(r, 8)
        status = CHECKLIST_STATUS_MAP.get(r[2], r[2])
        out.append([r[0], status, r[3], r[5], r[7]])
    return out


def extract_villa(service, sheet_id, villa):
    header_rows = read_range(service, sheet_id, villa, "A1:H14")
    header = parse_header_block(header_rows)
    header["sheet_name"] = villa
    header["header_a1"] = header_rows[0][0] if header_rows and header_rows[0] else ""

    notes_rows = read_range(service, sheet_id, villa, "A14:A17")
    header["notes"] = next(
        (r[0] for r in notes_rows if r and r[0].startswith("COMMISSIONING NOTES")), ""
    )

    header["checklist"] = extract_checklist(service, sheet_id, villa)
    header["keypads"] = extract_table(service, sheet_id, villa, "keypads")
    header["closeout"] = extract_table(service, sheet_id, villa, "closeout")
    header["mods_out"] = extract_table(service, sheet_id, villa, "mods_out")
    header["lamps"] = extract_table(service, sheet_id, villa, "lamps")
    header["modreg"] = extract_table(service, sheet_id, villa, "modreg")

    for field in ("kp_act", "kp_test", "tasks_pass", "open_defects", "dim_mod", "sw_mod"):
        header[field] = int(header[field]) if header[field] != "" else 0
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
