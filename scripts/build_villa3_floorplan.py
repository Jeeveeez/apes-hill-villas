#!/usr/bin/env python3
"""Builds site/villa-3/floor-plan.html -- the second villa to get the full
Designer-report treatment (engravings + an interactive floor plan), after
Villa 15.

The physical floor plan, keypad numbering (KP1..KP25, KP-GARAGE), load
numbering (L01..L51) and keypad engraving layout are all confirmed
IDENTICAL across villas (same construction template) -- verified by
diffing Villa 3's Report Package engraving pages and Load Schedule
against Villa 15's. So the pin GEOMETRY (data/floorplan_pins.json), the
engraving button groups, and the load schedule's zone/name/wattage/panel
assignment are all reused verbatim from Villa 15's build; only the
per-device STATUS (pass/pending) is Villa 3's own, pulled from its
already-fetched data/villas_extract.json.

Not part of the regular generate_villas.py/generate_fleet.py pipeline --
like Villa 15, this is a one-off build, run again by hand if Villa 3's
keypad/load test results change materially enough to be worth a refresh.
"""
import html as H
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
DATA_DIR = REPO_ROOT / "data"


def esc(s):
    return H.escape(str(s), quote=True)


PINS = json.load(open(DATA_DIR / "floorplan_pins.json"))

# ---- Engraving groups: confirmed byte-identical to Villa 15 (same labels,
# same keypad-id groupings) by reading Villa 3's own Engraving section.
BOM_DESC = {
    'HQWD-W4BS-WH': 'HWQS Designer Wired seeTouch 4 Button Keypad',
    'HQWD-W5B-WH': 'HWQS Designer Wired seeTouch 5 Button Keypad',
    'HQWD-W6B-WH': 'HWQS Designer Wired seeTouch 6 Button Keypad',
    'HQWD-W1B-WH': 'HWQS Designer Wired seeTouch 1 Button Keypad',
    'HQR-3PD-1-SW': 'HWQS RF 1 Outlet 300 W Plug-in Dimmer',
    'LQSE-4A5-120-D': 'DIN Rail Power Module LED+ Adaptive 4 Output',
    'LQSE-4S8-120-D': 'DIN Rail Power Module Switching 8A 4 Output',
    'HQP7-2': 'HomeWorks QSX 2-Link Processor',
    'HQR-REP-120': 'HWQS Hybrid Wired/Wireless RF System Repeater',
}

ENGRAVING_GROUPS = [
    {'key': 'A', 'locations': ['KP10'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 4, 'labels': ['Home', 'Foyer', 'Evening', 'Away']}]},
    {'key': 'B', 'locations': ['KP14', 'KP16'], 'wallplate': 'CW-2-WH', 'color': 'White', 'backbox': '2',
     'devices': [
         {'buttons': 5, 'labels': ['Terrace On', 'Terrace Fan', 'Pendant', 'Pool', 'All Ext Off']},
         {'buttons': 6, 'labels': ['On/Off', 'Evening', 'Kitchen', 'Counter', 'Pendant', 'Fan']},
     ]},
    {'key': 'C', 'locations': ['KP15'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 6, 'labels': ['On/Off', 'Evening', 'Kitchen', 'Counter', 'Pendant', 'Fan']}]},
    {'key': 'D', 'locations': ['KP12', 'KP23', 'KP21', 'KP6', 'KP3'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 4, 'labels': ['On', 'Evening', 'Fan', 'Off']}]},
    {'key': 'E', 'locations': ['KP17', 'KP13'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 6, 'labels': ['On', 'Evening', 'Pendant', 'Fan', 'Pool', 'Off']}]},
    {'key': 'F', 'locations': ['KP-GARAGE'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 1, 'labels': ['On/Off']}]},
    {'key': 'G', 'locations': ['KP22', 'KP18', 'KP5', 'KP4'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 6, 'labels': ['On', 'Evening', 'Fan', 'Closet', 'Lamps', 'Off']}]},
    {'key': 'H', 'locations': ['KP24', 'KP25', 'KP19', 'KP20', 'KP8', 'KP7', 'KP2', 'KP1'], 'wallplate': 'CW-1-WH', 'color': 'White', 'backbox': '1',
     'devices': [{'buttons': 6, 'labels': ['On', 'Evening', 'Bedside', 'Floor Lamp', 'Fan', 'Off']}]},
]
KP_TO_GROUP = {}
for grp in ENGRAVING_GROUPS:
    for loc in grp['locations']:
        KP_TO_GROUP[loc] = grp


def engraving_for_gang(kp_id, model):
    grp = KP_TO_GROUP.get(kp_id)
    if not grp:
        return None
    m = re.search(r'W(\d+)B', model)
    buttons = int(m.group(1)) if m else None
    for dev in grp['devices']:
        if dev['buttons'] == buttons or len(grp['devices']) == 1:
            return {'wallplate': grp['wallplate'], 'color': grp['color'], 'backbox': grp['backbox'],
                    'buttons': dev['buttons'], 'labels': dev['labels']}
    return None


def engraving_image_for(kp_id):
    grp = KP_TO_GROUP.get(kp_id)
    if not grp:
        return None
    return {
        'src': f"assets/engravings/eng_{grp['key']}.png",
        'caption': f"Wallplate {grp['wallplate']} &middot; {grp['color']} &middot; backbox {grp['backbox']}",
    }


# ---- Load schedule: zone/name/type/wattage/panel assignment, confirmed
# identical across villas (same physical design); reused verbatim from
# Villa 15. Only each circuit's PASS/PENDING status is Villa 3's own.
LOAD_SCHEDULE = {
    'L01': {'zone': 'Bedroom 4', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 153, 'assigned': 'Panel 001 · Adaptive(8) · Output 1'},
    'L02': {'zone': 'Bedroom 4', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(2) · Output 4'},
    'L03': {'zone': 'Bathroom 4', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 4'},
    'L04': {'zone': 'Bathroom 4', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 136, 'assigned': 'Panel 001 · Adaptive(8) · Output 2'},
    'L05': {'zone': 'Bathroom 4', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 4'},
    'L06': {'zone': 'Bedroom 4', 'name': 'Lamps', 'type': 'LED Reverse Phase', 'watt': 114, 'assigned': 'Panel 001 · Adaptive(5) · Output 4'},
    'L07': {'zone': 'Bedroom 4 Closet', 'name': 'Closet', 'type': 'LED Reverse Phase', 'watt': 68, 'assigned': 'Panel 001 · Adaptive(8) · Output 3'},
    'L08': {'zone': 'Bedroom 1', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 153, 'assigned': 'Panel 001 · Adaptive(4) · Output 1'},
    'L09': {'zone': 'Bedroom 3 Closet', 'name': 'Closet', 'type': 'LED Reverse Phase', 'watt': 68, 'assigned': 'Panel 001 · Adaptive(7) · Output 3'},
    'L10': {'zone': 'Bathroom 3', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 136, 'assigned': 'Panel 001 · Adaptive(7) · Output 2'},
    'L11': {'zone': 'Bedroom 3', 'name': 'Lamps', 'type': 'LED Reverse Phase', 'watt': 114, 'assigned': 'Panel 001 · Adaptive(5) · Output 3'},
    'L12': {'zone': 'Bathroom 3', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 3'},
    'L13': {'zone': 'Bathroom 3', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 3'},
    'L14': {'zone': 'Bedroom 3', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 153, 'assigned': 'Panel 001 · Adaptive(7) · Output 1'},
    'L15': {'zone': 'Bedroom 3', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(2) · Output 3'},
    'L16': {'zone': 'Bedroom 1', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(2) · Output 1'},
    'L17': {'zone': 'Kitchen/Living Room', 'name': 'North Hall', 'type': 'LED Reverse Phase', 'watt': 23, 'assigned': 'Panel 001 · Adaptive(1) · Output 3'},
    'L18': {'zone': 'Foyer', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 119, 'assigned': 'Panel 001 · Adaptive(1) · Output 2'},
    'L19': {'zone': 'Entrance', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 136, 'assigned': 'Panel 001 · Adaptive(1) · Output 1'},
    'L20': {'zone': 'Laundry', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 34, 'assigned': None},
    'L21': {'zone': 'Laundry', 'name': 'Extractor Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(3) · Output 2'},
    'L22': {'zone': 'WC', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 34, 'assigned': 'Panel 001 · Adaptive(1) · Output 4'},
    'L23': {'zone': 'WC', 'name': 'Extractor Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(3) · Output 1'},
    'L24': {'zone': 'Patio', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 221, 'assigned': 'Panel 001 · Adaptive(3) · Output 1'},
    'L25': {'zone': 'Patio', 'name': 'Fans', 'type': 'Fan Switched', 'watt': 400, 'assigned': 'Panel 002 · Switch(1) · Output 3'},
    'L26': {'zone': 'Patio', 'name': 'Pendants', 'type': 'LED Reverse Phase', 'watt': 57, 'assigned': 'Panel 001 · Adaptive(3) · Output 2'},
    'L27': {'zone': 'Patio', 'name': 'Pendants', 'type': 'LED Reverse Phase', 'watt': 57, 'assigned': 'Panel 001 · Adaptive(3) · Output 2'},
    'L28': {'zone': 'Patio', 'name': 'Fans', 'type': 'Fan Switched', 'watt': 400, 'assigned': 'Panel 002 · Switch(1) · Output 3'},
    'L29': {'zone': 'Patio', 'name': 'Fans', 'type': 'Fan Switched', 'watt': None, 'assigned': 'Panel 002 · Switch(1) · Output 4'},
    'L30': {'zone': 'Patio', 'name': 'Fans', 'type': 'Fan Switched', 'watt': None, 'assigned': 'Panel 002 · Switch(1) · Output 4'},
    'L32': {'zone': 'Kitchen/Living Room', 'name': 'Fans', 'type': 'Fan Switched', 'watt': 200, 'assigned': 'Panel 002 · Switch(1) · Output 1'},
    'L33': {'zone': 'Kitchen/Living Room', 'name': 'Fans', 'type': 'Fan Switched', 'watt': 200, 'assigned': 'Panel 002 · Switch(1) · Output 1'},
    'L34': {'zone': 'Kitchen/Living Room', 'name': 'Pendant', 'type': 'LED Reverse Phase', 'watt': 115, 'assigned': 'Panel 001 · Adaptive(2) · Output 1'},
    'L35': {'zone': 'Kitchen/Living Room', 'name': 'Counter/Extractor Fan', 'type': 'LED Switched', 'watt': 85, 'assigned': 'Panel 001 · Adaptive(2) · Output 2'},
    'L36': {'zone': 'Kitchen/Living Room', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 374, 'assigned': 'Panel 001 · Adaptive(2) · Output 4'},
    'L37': {'zone': 'Kitchen/Living Room', 'name': 'Fans', 'type': 'Fan Switched', 'watt': None, 'assigned': 'Panel 002 · Switch(1) · Output 2'},
    'L38': {'zone': 'Kitchen/Living Room', 'name': 'Fans', 'type': 'Fan Switched', 'watt': None, 'assigned': 'Panel 002 · Switch(1) · Output 2'},
    'L39': {'zone': 'Kitchen/Living Room', 'name': 'South Hall', 'type': 'LED Reverse Phase', 'watt': 23, 'assigned': 'Panel 001 · Adaptive(2) · Output 3'},
    'L40': {'zone': 'Bedroom 2 Closet', 'name': 'Closet', 'type': 'LED Reverse Phase', 'watt': 68, 'assigned': 'Panel 001 · Adaptive(6) · Output 3'},
    'L41': {'zone': 'Bedroom 2', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(2) · Output 2'},
    'L42': {'zone': 'Bedroom 2', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 153, 'assigned': 'Panel 001 · Adaptive(6) · Output 1'},
    'L43': {'zone': 'Bedroom 2', 'name': 'Lamps', 'type': 'LED Reverse Phase', 'watt': 114, 'assigned': 'Panel 001 · Adaptive(5) · Output 2'},
    'L44': {'zone': 'Bathroom 2', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 136, 'assigned': 'Panel 001 · Adaptive(6) · Output 2'},
    'L45': {'zone': 'Bathroom 2', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 2'},
    'L46': {'zone': 'Bathroom 2', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 2'},
    'L47': {'zone': 'Bedroom 1 Closet', 'name': 'Closet', 'type': 'LED Reverse Phase', 'watt': 68, 'assigned': 'Panel 001 · Adaptive(4) · Output 3'},
    'L48': {'zone': 'Bathroom 1', 'name': 'Downlights', 'type': 'LED Reverse Phase', 'watt': 136, 'assigned': 'Panel 001 · Adaptive(4) · Output 2'},
    'L49': {'zone': 'Bedroom 1', 'name': 'Lamps', 'type': 'LED Reverse Phase', 'watt': 114, 'assigned': 'Panel 001 · Adaptive(5) · Output 1'},
    'L50': {'zone': 'Patio', 'name': 'Pool', 'type': 'Inc/Halogen Switched', 'watt': 20, 'assigned': 'Panel 001 · Adaptive(3) · Output 3', 'feed': 'PSP 18'},
    'L51': {'zone': 'Bathroom 1', 'name': 'Fan', 'type': 'Fan Switched', 'watt': 100, 'assigned': 'Panel 002 · Switch(4) · Output 1'},
}
LOAD_SCHEDULE_NOTE = {
    'L31': "L31 does not appear anywhere in the Lutron Designer load schedule for Villa 3 — it isn’t configured as a load in the system, not just unrecorded in the tracker.",
}

# ---- Villa 3's own device status, from the tracker (already fetched into
# data/villas_extract.json by fetch_sheet_data.py / generate_villas.py).
extract = json.load(open(DATA_DIR / "villas_extract.json"))
v3 = extract["Villa 3"]

KP = {}
for dev, loc, model, serial, act, test, find in v3["keypads"]:
    # Villa 3's tracker labels a 2-gang wallplate's two devices as
    # "KP14 / Gang 1" and "KP14 / Gang 2" rather than two plain ids --
    # group them under the shared pin id "KP14".
    pin_id = dev.split(" / Gang")[0].strip()
    KP.setdefault(pin_id, {"gangs": []})["gangs"].append({
        "device": dev, "location": loc, "model": model, "serial": serial,
        "activated": act, "tested": test, "findings": find,
    })

L = {lid: {"entries": []} for lid in LOAD_SCHEDULE}
for panel, module, model, outp, load_desc, wmatch, ftest, notes in v3["mods_out"]:
    ids_here = []
    for m in re.finditer(r'L(\d{2})(?:/L?(\d{2}))?', load_desc):
        ids_here.append('L' + m.group(1))
        if m.group(2):
            ids_here.append('L' + m.group(2))
    for lid in ids_here:
        L.setdefault(lid, {"entries": []})["entries"].append({
            "panel": panel, "module": module, "output": outp, "load": load_desc,
            "wiring_match": wmatch, "func_test": ftest, "notes": notes,
        })


def kp_status(entry):
    gangs = entry["gangs"]
    if gangs and all(g["activated"] == "Pass" and g["tested"] == "Pass" for g in gangs):
        return "pass"
    return "pend"


def l_status(entry):
    entries = entry["entries"]
    if not entries:
        return "nr"
    if any(e["func_test"] == "Fail" or e["wiring_match"] == "Review" for e in entries):
        return "fail"
    if all(e["wiring_match"] == "Pass" and e["func_test"] == "Pass" for e in entries):
        return "pass"
    return "pend"


pin_buttons = []
for p in PINS["kp"] + [dict(x, kind="l") for x in PINS["l"]]:
    pid = p["id"]
    kind = p.get("kind", "kp" if pid.startswith("KP") else "l")
    x, y = p["x"], p["y"]
    st = kp_status(KP[pid]) if kind == "kp" else l_status(L.get(pid, {"entries": []}))
    extra = " pin-est" if p.get("estimated") else ""
    shape = "pin-kp" if kind == "kp" else "pin-l"
    inner = esc(pid.replace("KP", "")) if kind == "kp" else ""
    pin_buttons.append(
        f'<button type="button" class="pin {shape} pin-{st}{extra}" '
        f'style="left:{x}%; top:{y}%" data-kind="{kind}" data-id="{esc(pid)}" '
        f'data-tip="{esc(pid)}" aria-label="{esc(pid)}">{inner}</button>'
    )

detail = {}
for pid, entry in KP.items():
    for g in entry["gangs"]:
        g["model_desc"] = BOM_DESC.get(g["model"])
        g["engraving"] = engraving_for_gang(pid, g["model"])
    detail[pid] = {
        "kind": "kp", "id": pid, "status": kp_status(entry),
        "gangs": entry["gangs"],
        "engraving_image": engraving_image_for(pid),
    }
for pid, entry in L.items():
    fixture = LOAD_SCHEDULE.get(pid)
    detail[pid] = {
        "kind": "l", "id": pid, "status": l_status(entry),
        "fixture": fixture,
        "fixture_note": LOAD_SCHEDULE_NOTE.get(pid),
        "entries": entry["entries"],
    }

# ---- Garage & Technical Room cards (not on the main floor plan -- its own
# inset drawing on the electrical sheet, same as Villa 15).
garage_kp_html = ""
if "KP-GARAGE" in KP:
    g = KP["KP-GARAGE"]["gangs"][0]
    eg = engraving_for_gang("KP-GARAGE", g["model"])
    eg_note = f" &middot; Engraved &ldquo;{esc('/'.join(eg['labels']))}&rdquo;" if eg else ""
    garage_kp_html = f'''<div class="supp-row">
      <div class="supp-id mono">KP-GARAGE</div>
      <div>
        <div>{esc(g['location'])}</div>
        <div class="cell-note">{esc(g['model'])} &middot; {esc(g['serial'])}{eg_note}</div>
      </div>
      <span class="badge b-{'pass' if g['activated']=='Pass' and g['tested']=='Pass' else 'pend'}">{esc(g['activated'])}</span>
    </div>'''

garage_row = next((r for r in v3["mods_out"] if r[4].startswith("Garage")), None)
garage_l_html = ""
if garage_row:
    panel, module, model, out, load_desc, wmatch, ftest, notes = garage_row
    badge_cls = "pass" if ftest == "Pass" else ("fail" if ftest == "Fail" else "nr")
    row_cls = " supp-row-fail" if badge_cls == "fail" else ""
    garage_l_html = f'''<div class="supp-row{row_cls}">
  <div class="supp-id mono">{esc(out)}</div>
  <div>
    <div>{esc(load_desc)}</div>
    <div class="cell-note">{esc(notes)}</div>
  </div>
  <span class="badge b-{badge_cls}">{esc(ftest)}</span>
</div>'''

TEMPLATE = r"""<title>Villa 3 Floor Plan</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#070B1A; --surface:#111A38; --surface-2:#0C1230;
  --ink:#FFFFFF; --muted:#8E9BC0; --line:#232C52;
  --accent:#0080CB; --accent-ink:#4FA8E0;
  --pass:#5FC093; --pass-bg:#15362C;
  --pend:#E0A94B; --pend-bg:#3A2E12;
  --fail:#E8796A; --fail-bg:#3D1C17;
  --nr:#8C9DAD;  --nr-bg:#1B3146;
  --f-display:"Inter",system-ui,sans-serif;
  --f-body:"Inter",system-ui,sans-serif;
  --f-mono:"IBM Plex Mono","SF Mono",monospace;
  color-scheme: dark;
}
*{box-sizing:border-box;}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--f-body); font-size:15px; line-height:1.5;
  padding-left:max(16px, env(safe-area-inset-left,0px));
  padding-right:max(16px, env(safe-area-inset-right,0px));
}
body::before{
  content:""; position:fixed; inset:0 0 auto; height:env(safe-area-inset-top,0px);
  z-index:20; background:var(--surface);
}
a{color:var(--accent);}
h1,h2,h3{text-wrap:balance; margin:0;}
.wrap{max-width:1280px; margin:0 auto; padding-block:0 48px;}

.topbar{
  position:sticky; top:env(safe-area-inset-top,0px); z-index:25;
  background:var(--surface); border-bottom:1px solid var(--line); padding-block:10px;
}
.topbar-inner{max-width:1280px; margin:0 auto; display:flex; align-items:center; gap:14px; flex-wrap:wrap;}
.topbar-brand{display:flex; align-items:center; gap:9px;}
.topbar-brand img{height:22px; width:auto; display:block;}
.topbar-title{font-family:var(--f-display); font-weight:600; font-size:19px; letter-spacing:.02em; white-space:nowrap;}
.topbar-title b{color:var(--accent-ink);}
.topbar-nav-buttons{display:flex; gap:8px; flex:none;}
.btn{
  display:inline-flex; align-items:center; gap:6px; white-space:nowrap;
  font-family:var(--f-display); font-size:12px; font-weight:600; letter-spacing:.03em;
  text-decoration:none; padding:6px 12px; border-radius:999px;
  background:var(--surface-2); color:var(--ink); border:1px solid var(--line);
  transition:background .15s ease, border-color .15s ease, color .15s ease, transform .1s ease;
}
.btn:hover{background:var(--surface); border-color:var(--accent-ink); color:var(--accent-ink); transform:translateY(-1px);}
.btn-primary{background:var(--accent); color:#fff; border-color:var(--accent);}
.btn-primary:hover{background:var(--accent-ink); border-color:var(--accent-ink); color:#fff;}
.search-box{
  display:flex; align-items:center; gap:6px; background:var(--surface-2);
  border:1px solid var(--line); border-radius:7px; padding:6px 10px; min-width:170px; margin-left:auto;
}
.search-box svg{flex:none; opacity:.55;}
.search-box input{border:none; background:transparent; outline:none; color:var(--ink); font-family:var(--f-body); font-size:13.5px; width:100%;}
.search-box input::placeholder{color:var(--muted);}

.hero{padding-block:24px 16px;}
.eyebrow{font-family:var(--f-display); font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); font-weight:600;}
h1.page-title{font-family:var(--f-display); font-size:38px; font-weight:300; letter-spacing:-.005em; margin-top:2px;}
.hero-sub{color:var(--muted); font-size:14px; margin-top:6px; max-width:68ch;}

.toolbar{
  display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-block:16px;
  background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:10px 14px;
}
.toolbar-group{display:flex; align-items:center; gap:6px;}
.toolbar-label{font-family:var(--f-display); font-size:11.5px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin-right:2px;}
.layer-btn{
  font-family:var(--f-display); font-size:13px; letter-spacing:.02em; font-weight:600;
  border:1px solid var(--line); background:var(--surface-2); color:var(--muted);
  border-radius:7px; padding:6px 12px; cursor:pointer; display:flex; align-items:center; gap:7px;
}
.layer-btn .sw{width:10px; height:10px; border-radius:3px; flex:none;}
.layer-btn[aria-pressed="true"]{color:var(--ink); border-color:var(--accent); background:color-mix(in srgb, var(--accent) 12%, var(--surface));}
.zoom-btn{
  font-family:var(--f-mono); font-size:15px; width:30px; height:30px; border-radius:7px;
  border:1px solid var(--line); background:var(--surface-2); color:var(--ink); cursor:pointer;
}
.zoom-level{font-family:var(--f-mono); font-size:12.5px; color:var(--muted); min-width:38px; text-align:center;}
.toolbar-spacer{flex:1 1 auto;}
.hint{font-size:12px; color:var(--muted);}

.plan-shell{position:relative;}
.plan-viewport{
  position:relative; border:1px solid var(--line); border-radius:10px; overflow:auto;
  background:var(--surface); max-height:76vh; touch-action:pan-x pan-y;
}
.plan-stage{position:relative; width:1300px; max-width:none;}
.plan-stage img{display:block; width:100%; height:auto; user-select:none; -webkit-user-drag:none; pointer-events:none;}

.pin{
  position:absolute; transform:translate(-50%,-50%); border:none; cursor:pointer; padding:0;
  font-family:var(--f-mono); font-weight:700; color:#fff; line-height:1;
  box-shadow:0 0 0 2px #fff, 0 1px 3px rgba(0,0,0,.35); z-index:2;
}
.pin:hover, .pin:focus-visible{z-index:10; transform:translate(-50%,-50%) scale(1.3);}
.pin-kp{width:21px; height:21px; border-radius:4px; font-size:9px; display:flex; align-items:center; justify-content:center;}
.pin-l{width:11px; height:11px; border-radius:50%;}
.pin-pass{background:var(--pass);}
.pin-pend{background:var(--pend);}
.pin-fail{background:var(--fail); animation:pulse 1.8s ease-in-out infinite;}
.pin-nr{background:var(--nr);}
.pin-est{box-shadow:0 0 0 2px #fff, 0 0 0 4px var(--accent);}
.pin.is-open{z-index:11; transform:translate(-50%,-50%) scale(1.3); box-shadow:0 0 0 2px #fff, 0 0 0 4px var(--accent-ink);}
@keyframes pulse{0%,100%{box-shadow:0 0 0 2px #fff, 0 1px 3px rgba(0,0,0,.35);} 50%{box-shadow:0 0 0 2px #fff, 0 0 0 6px color-mix(in srgb, var(--fail) 45%, transparent);}}
.pin[data-tip]:hover::after, .pin[data-tip]:focus-visible::after{
  content:attr(data-tip); position:absolute; bottom:135%; left:50%; transform:translateX(-50%);
  background:var(--ink); color:var(--bg); font-family:var(--f-mono); font-size:11px; font-weight:500;
  padding:3px 7px; border-radius:5px; white-space:nowrap; pointer-events:none; z-index:30;
}
.pin.is-dim{opacity:.22;}
[data-hide-kp="true"] .pin-kp{display:none;}
[data-hide-l="true"] .pin-l{display:none;}

.legend-overlay{
  position:absolute; left:14px; bottom:14px; z-index:8; background:var(--surface);
  border:1px solid var(--line); border-radius:10px; padding:10px 13px; width:220px;
  box-shadow:0 4px 16px rgba(0,0,0,.14);
}
.legend-head{display:flex; align-items:center; justify-content:space-between; gap:8px; cursor:pointer; user-select:none;}
.legend-title{font-family:var(--f-display); font-size:11.5px; letter-spacing:.07em; text-transform:uppercase; color:var(--muted);}
.legend-toggle{background:none; border:none; color:var(--muted); font-size:15px; cursor:pointer; line-height:1; padding:2px;}
.legend-body{margin-top:7px; display:flex; flex-direction:column; gap:2px;}
.legend-overlay.collapsed .legend-body{display:none;}
.legend-group{display:flex; flex-direction:column; gap:2px; padding-block:3px;}
.legend-group + .legend-group{border-top:1px solid var(--line); margin-top:3px; padding-top:6px;}
.legend-row{display:flex; align-items:center; gap:8px; font-size:12px;}
.legend-sw{width:12px; height:12px; border-radius:4px; flex:none; box-shadow:0 0 0 1px var(--line) inset; background:var(--muted);}
.legend-sw.round{width:9px; height:9px; border-radius:50%;}
.legend-sw.est{box-shadow:0 0 0 2px var(--accent); background:transparent;}
.legend-note{font-size:11px; color:var(--muted); margin-top:5px; line-height:1.5; padding-top:6px; border-top:1px dashed var(--line);}

.popup{
  position:absolute; z-index:40; background:var(--surface); border:1px solid var(--line); border-radius:10px;
  box-shadow:0 10px 28px rgba(0,0,0,.2); padding:14px 16px; width:280px; max-height:380px; overflow-y:auto;
}
.popup[hidden]{display:none;}
.popup-close{
  position:absolute; top:8px; right:8px; width:22px; height:22px; border-radius:50%; border:none;
  background:var(--surface-2); color:var(--muted); font-size:14px; line-height:1; cursor:pointer;
}
.popup .detail-head{padding-right:22px;}
.popup-img{max-width:100%; max-height:230px; width:auto; height:auto; display:block; margin:4px auto 2px; border-radius:6px;}
.popup-img-cap{font-size:11px; color:var(--muted); text-align:center; margin-bottom:4px;}

.detail-empty{color:var(--muted); font-size:13.5px; line-height:1.6;}
.detail-head{display:flex; align-items:center; gap:9px; margin-bottom:10px;}
.detail-id{font-family:var(--f-mono); font-size:17px; font-weight:500;}
.detail-section{border-top:1px solid var(--line); padding-top:10px; margin-top:10px;}
.detail-section:first-of-type{border-top:none; margin-top:0; padding-top:0;}
.detail-label{font-family:var(--f-display); font-size:11px; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); margin-bottom:3px;}
.detail-field{font-size:13.5px; margin-bottom:6px;}
.detail-note{font-size:12.5px; color:var(--muted); margin-top:3px; line-height:1.5;}
.kv-grid{display:grid; grid-template-columns:auto 1fr; gap:3px 10px; font-size:12.5px; margin-top:4px;}
.kv-grid dt{color:var(--muted);}
.kv-grid dd{margin:0; font-family:var(--f-mono);}
.badge{display:inline-flex; align-items:center; gap:5px; font-family:var(--f-display); font-size:12px; letter-spacing:.03em; font-weight:600; padding:3px 9px; border-radius:999px;}
.b-pass{background:var(--pass-bg); color:var(--pass);}
.b-pend{background:var(--pend-bg); color:var(--pend);}
.b-fail{background:var(--fail-bg); color:var(--fail);}
.b-nr{background:var(--nr-bg); color:var(--nr);}
.mono{font-family:var(--f-mono); font-variant-numeric:tabular-nums;}

.supp{margin-top:22px;}
.supp-head{display:flex; align-items:baseline; gap:12px; margin-bottom:12px; flex-wrap:wrap;}
.supp-head h2{font-family:var(--f-display); font-size:22px; font-weight:600;}
.supp-head .hint{margin-left:auto;}
.supp-grid{display:grid; grid-template-columns:1fr 1fr; gap:12px;}
.supp-row{display:grid; grid-template-columns:90px 1fr auto; gap:12px; align-items:start; padding:14px 16px; background:var(--surface); border:1px solid var(--line); border-radius:10px;}
.supp-row-fail{border-color:color-mix(in srgb, var(--fail) 45%, var(--line)); background:var(--fail-bg);}
.supp-id{font-size:13px; padding-top:2px;}
.cell-note{font-size:12.5px; color:var(--muted); margin-top:3px;}

footer{padding-block:30px 10px; font-size:12.5px; color:var(--muted); border-top:1px solid var(--line); margin-top:10px;}

@media (max-width:900px){
  .supp-grid{grid-template-columns:1fr;}
  h1.page-title{font-size:30px;}
}
@media (max-width:640px){
  .legend-overlay{width:168px; padding:8px 10px;}
  .popup{width:232px;}
}
</style>

<div class="topbar">
  <div class="topbar-inner">
    <div class="topbar-brand"><img src="../assets/logo.png" alt="MNE Innovations"><div class="topbar-title">VILLA <b>3</b> &middot; Floor Plan</div></div>
    <div class="topbar-nav-buttons">
      <a class="btn" href="../index.html">&larr; All Villas</a>
      <a class="btn" href="status.html">Status</a>
      <a class="btn btn-primary" href="technical-record.html">Technical Record</a>
    </div>
    <div class="search-box">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
      <input id="search" type="search" placeholder="Jump to KP or L number&hellip;" aria-label="Find a pin">
    </div>
  </div>
</div>

<div class="wrap">
  <section class="hero">
    <div class="eyebrow">Apes Hill Hilltop Villas &middot; Ground Floor</div>
    <h1 class="page-title">Keypad &amp; Circuit Map</h1>
    <p class="hero-sub">Every marker sits at its drawn position on electrical sheet A-E-2.01 rev. 11. Click a marker for its commissioning record; the floor plan is identical across all 14 villas, carried forward from Villa 15's documentation.</p>
  </section>

  <div class="toolbar">
    <div class="toolbar-group">
      <span class="toolbar-label">Layers</span>
      <button class="layer-btn" id="toggle-kp" aria-pressed="true" type="button"><span class="sw" style="background:var(--pass); border-radius:3px;"></span>Keypads (23)</button>
      <button class="layer-btn" id="toggle-l" aria-pressed="true" type="button"><span class="sw" style="background:var(--pass); border-radius:50%;"></span>Light circuits (51)</button>
    </div>
    <div class="toolbar-group">
      <span class="toolbar-label">Zoom</span>
      <button class="zoom-btn" id="zoom-out" type="button" aria-label="Zoom out">&minus;</button>
      <span class="zoom-level" id="zoom-level">1300px</span>
      <button class="zoom-btn" id="zoom-in" type="button" aria-label="Zoom in">+</button>
    </div>
    <div class="toolbar-spacer"></div>
    <span class="hint">Drawing ref: A-E-2.01 rev. 11, M&amp;E Partners Ltd &middot; scale 1:50</span>
  </div>

  <div class="plan-shell">
    <div class="plan-viewport" id="viewport">
      <div class="plan-stage" id="stage">
        <img src="../assets/plan_bg.png" alt="Villa ground floor lighting and switching layout" draggable="false">
        __PINS__
      </div>
    </div>

    <div class="legend-overlay" id="legend">
      <div class="legend-head" id="legend-head">
        <span class="legend-title">Legend</span>
        <button class="legend-toggle" id="legend-toggle" type="button" aria-label="Toggle legend">&minus;</button>
      </div>
      <div class="legend-body">
        <div class="legend-group">
          <div class="legend-row"><span class="legend-sw"></span>Keypad</div>
          <div class="legend-row"><span class="legend-sw round"></span>Light / fan circuit</div>
        </div>
        <div class="legend-group">
          <div class="legend-row"><span class="legend-sw" style="background:var(--pass)"></span>Pass</div>
          <div class="legend-row"><span class="legend-sw" style="background:var(--pend)"></span>Pending</div>
          <div class="legend-row"><span class="legend-sw" style="background:var(--fail)"></span>Needs review</div>
          <div class="legend-row"><span class="legend-sw" style="background:var(--nr)"></span>Not in output table</div>
          <div class="legend-row"><span class="legend-sw round est"></span>Position estimated</div>
        </div>
        <div class="legend-note">L20 &amp; L31 are drawn but not in Villa 3&rsquo;s Section 4 output table &mdash; a template-wide gap, not a Villa 3-specific issue.</div>
      </div>
    </div>

    <div class="popup" id="popup" hidden>
      <button class="popup-close" id="popup-close" type="button" aria-label="Close">&times;</button>
      <div id="popup-body"></div>
    </div>
  </div>

  <section class="supp">
    <div class="supp-head">
      <h2>Garage &amp; Technical Room</h2>
      <span class="hint">Separate inset drawings on sheet A-E-2.01 &mdash; not to the same scale as the main plan above</span>
    </div>
    <div class="supp-grid">
      __GARAGE_KP__
      __GARAGE_L__
    </div>
  </section>

  <footer>
    Marker positions extracted from the vector text layer of A-E-2.01 rev. 11, reused from Villa 15 (identical floor plan).
    Device data: Apes Hill Hilltop Villas Master Commissioning Tracker, "Villa 3" tab, Section 2 &amp; Section 4.
  </footer>
</div>

<script id="detail-data" type="application/json">__DETAIL_JSON__</script>
<script>
(function(){
  var DATA = JSON.parse(document.getElementById('detail-data').textContent);
  var shell = document.querySelector('.plan-shell');
  var viewport = document.getElementById('viewport');
  var stage = document.getElementById('stage');
  var popup = document.getElementById('popup');
  var popupBody = document.getElementById('popup-body');
  var zoomLevels = [900, 1300, 1800, 2400, 3100];
  var zoomIdx = 1;
  var openPinId = null;

  function buildPopupHTML(id){
    var d = DATA[id];
    if(!d){ return '<div class="detail-empty">No record for '+id+'.</div>'; }
    var html = '<div class="detail-head"><span class="detail-id mono">'+id+'</span>'+badge(d.status)+'</div>';
    if (d.kind === 'kp'){
      if (d.engraving_image){
        html += '<img class="popup-img" src="'+d.engraving_image.src+'" alt="'+id+' keypad engraving">';
        html += '<div class="popup-img-cap">'+d.engraving_image.caption+'</div>';
      }
      d.gangs.forEach(function(g){
        html += '<div class="detail-section">';
        html += '<div class="detail-label">'+(g.device)+'</div>';
        html += '<div class="detail-field">'+g.location+'</div>';
        html += '<div class="detail-field mono">'+g.model+' &middot; '+g.serial+'</div>';
        if (g.model_desc) html += '<div class="detail-note">'+g.model_desc+'</div>';
        html += '<div class="detail-field">Activated '+badge(g.activated==='Pass'?'pass':'pend', g.activated)+' &nbsp; Tested '+badge(g.tested==='Pass'?'pass':'pend', g.tested)+'</div>';
        if (g.findings) html += '<div class="detail-note">'+g.findings+'</div>';
        html += '</div>';
      });
    } else {
      if (d.fixture){
        var f = d.fixture;
        html += '<div class="detail-section"><div class="detail-label">Fixture</div>';
        html += '<dl class="kv-grid">';
        html += '<dt>Zone</dt><dd>'+f.zone+'</dd>';
        html += '<dt>Load type</dt><dd>'+f.type+'</dd>';
        html += '<dt>Wattage</dt><dd>'+(f.watt!=null ? f.watt+' W' : 'Unspecified') +'</dd>';
        html += '<dt>Assigned to</dt><dd>'+(f.assigned || 'Unassigned') +'</dd>';
        html += '</dl></div>';
      }
      if (d.fixture_note){
        html += '<div class="detail-section"><div class="detail-note">'+d.fixture_note+'</div></div>';
      }
      if (d.entries.length === 0 && !d.fixture){
        html += '<div class="detail-section"><div class="detail-note">This circuit is drawn on the sheet but has no row in Villa 3&rsquo;s Section 4 output-verification table.</div></div>';
      } else {
        d.entries.forEach(function(e){
          html += '<div class="detail-section">';
          html += '<div class="detail-label">'+e.panel+' &middot; '+e.module+' &middot; output '+e.output+'</div>';
          html += '<div class="detail-field">'+e.load+'</div>';
          html += '<div class="detail-field">Wiring '+badge(e.wiring_match==='Pass'?'pass':(e.wiring_match==='Review'?'fail':'nr'), e.wiring_match)+' &nbsp; Test '+badge(e.func_test==='Pass'?'pass':(e.func_test==='Fail'?'fail':'nr'), e.func_test)+'</div>';
          if (e.notes) html += '<div class="detail-note">'+e.notes+'</div>';
          html += '</div>';
        });
      }
    }
    return html;
  }
  function badge(cls, text){
    text = text || ({pass:'Pass',pend:'Pending',fail:'Review',nr:'N/A'})[cls];
    return '<span class="badge b-'+cls+'">'+text+'</span>';
  }

  function findPin(id){ return viewport.querySelector('.pin[data-id="'+id+'"]'); }

  function positionPopup(pin){
    var shellRect = shell.getBoundingClientRect();
    var pinRect = pin.getBoundingClientRect();
    var px = pinRect.left - shellRect.left + pinRect.width/2;
    var py = pinRect.top - shellRect.top;
    var pw = popup.offsetWidth, ph = popup.offsetHeight;
    var left = Math.max(8, Math.min(px - pw/2, shellRect.width - pw - 8));
    var top = py - ph - 14;
    if (top < 8) top = py + 22;
    top = Math.max(8, Math.min(top, shellRect.height - ph - 8));
    popup.style.left = left + 'px';
    popup.style.top = top + 'px';
  }

  function openPopup(pin){
    var id = pin.getAttribute('data-id');
    popupBody.innerHTML = buildPopupHTML(id);
    popup.hidden = false;
    positionPopup(pin);
    document.querySelectorAll('.pin.is-open').forEach(function(p){p.classList.remove('is-open');});
    pin.classList.add('is-open');
    openPinId = id;
  }
  function closePopup(){
    popup.hidden = true;
    document.querySelectorAll('.pin.is-open').forEach(function(p){p.classList.remove('is-open');});
    openPinId = null;
  }

  viewport.addEventListener('click', function(ev){
    var pin = ev.target.closest('.pin');
    if(!pin){ closePopup(); return; }
    if (pin.getAttribute('data-id') === openPinId){ closePopup(); return; }
    openPopup(pin);
  });
  document.getElementById('popup-close').addEventListener('click', closePopup);
  document.addEventListener('keydown', function(ev){ if (ev.key === 'Escape') closePopup(); });
  viewport.addEventListener('scroll', function(){
    if (openPinId){ var p = findPin(openPinId); if (p) positionPopup(p); }
  });

  function setZoom(idx){
    zoomIdx = Math.max(0, Math.min(zoomLevels.length-1, idx));
    stage.style.width = zoomLevels[zoomIdx] + 'px';
    document.getElementById('zoom-level').textContent = zoomLevels[zoomIdx] + 'px';
    if (openPinId){ var p = findPin(openPinId); if (p) positionPopup(p); }
  }
  document.getElementById('zoom-in').addEventListener('click', function(){ setZoom(zoomIdx+1); });
  document.getElementById('zoom-out').addEventListener('click', function(){ setZoom(zoomIdx-1); });

  var legend = document.getElementById('legend');
  document.getElementById('legend-head').addEventListener('click', function(){
    var collapsed = legend.classList.toggle('collapsed');
    document.getElementById('legend-toggle').textContent = collapsed ? '+' : '−';
  });

  function toggleLayer(btn, attr){
    var pressed = btn.getAttribute('aria-pressed') === 'true';
    btn.setAttribute('aria-pressed', String(!pressed));
    stage.parentElement.setAttribute(attr, String(pressed));
  }
  document.getElementById('toggle-kp').addEventListener('click', function(){ toggleLayer(this, 'data-hide-kp'); });
  document.getElementById('toggle-l').addEventListener('click', function(){ toggleLayer(this, 'data-hide-l'); });

  var searchInput = document.getElementById('search');
  searchInput.addEventListener('input', function(){
    var q = searchInput.value.trim().toUpperCase();
    var pins = document.querySelectorAll('.pin');
    var firstMatch = null;
    pins.forEach(function(p){
      var id = p.getAttribute('data-id');
      var match = q.length > 0 && id.indexOf(q) !== -1;
      p.classList.toggle('is-dim', q.length > 0 && !match);
      if (match && !firstMatch) firstMatch = p;
    });
    if (firstMatch){ firstMatch.scrollIntoView({block:'center', inline:'center', behavior:'smooth'}); }
  });

  setZoom(1);
})();
</script>
"""

out = TEMPLATE
out = out.replace("__PINS__", "\n        ".join(pin_buttons))
out = out.replace("__GARAGE_KP__", garage_kp_html)
out = out.replace("__GARAGE_L__", garage_l_html)
out = out.replace("__DETAIL_JSON__", json.dumps(detail))


def wrap_page(html_fragment):
    idx = html_fragment.index("</style>") + len("</style>")
    head_part = html_fragment[:idx]
    body_part = html_fragment[idx:]
    title_m = re.search(r"<title>(.*?)</title>", head_part)
    title = title_m.group(1) if title_m else "Apes Hill Villas"
    head_part = re.sub(r"<title>.*?</title>\s*", "", head_part, count=1)
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<title>{title}</title>\n"
        f"{head_part}\n</head>\n<body>\n{body_part}\n</body>\n</html>\n"
    )


out_dir = SITE_DIR / "villa-3"
out_dir.mkdir(parents=True, exist_ok=True)
fname = out_dir / "floor-plan.html"
fname.write_text(wrap_page(out), encoding="utf-8")
print("wrote", fname)
