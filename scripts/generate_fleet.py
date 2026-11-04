#!/usr/bin/env python3
"""Generates the Fleet Dashboard (site/index.html) from data/villas_summary.json
(written by generate_villas.py) plus Villa 15's hand-curated summary and the
not-yet-started villas. Run generate_villas.py first so the summary file is
current."""
import html as H
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
DATA_DIR = REPO_ROOT / "data"


def esc(s):
    return H.escape(str(s), quote=True)


# Villa 15 has a richer, hand-curated technical record (keypad engravings,
# floor plan) that this pipeline doesn't regenerate yet -- see README.md.
# Its fleet-row figures are kept here until that page is folded into the
# same data-driven pipeline as the other villas.
VILLA15 = {
    "vnum": "15", "status": "Complete",
    "kp_act": 26, "kp_total": 26,
    "tasks_pass": 19, "tasks_total": 23,
    "open_issues": 3, "total_issues": 3,
    "technician": "Jeevan Panjwani",
    "report_package": "done",
    "status_url": "villa-15/status.html",
}

NOT_STARTED_VNUMS = ["8", "9", "10", "11", "12", "14", "16"]

PARCEL_ORDER = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "14", "15", "16"]

STATUS_BADGE = {"Complete": "b-pass", "In Progress": "b-pend", "Not Started": "b-nr"}


def render_row(v):
    vnum = v["vnum"]
    status = v["status"]
    linked = status != "Not Started"
    badge_cls = STATUS_BADGE.get(status, "b-nr")
    kp_pct = round(100 * v["kp_act"] / v["kp_total"]) if v["kp_total"] else 0
    task_pct = round(100 * v["tasks_pass"] / v["tasks_total"]) if v["tasks_total"] else 0
    kp_zero = " zero" if v["kp_act"] == 0 else ""
    task_zero = " zero" if v["tasks_pass"] == 0 else ""
    issues_cls = "issues-count has-issues" if v["open_issues"] else "issues-count"
    rp_cls = "rp-done" if v["report_package"] == "done" else "rp-pending"
    rp_label = "Processed" if v["report_package"] == "done" else "Pending"
    villa_id_cell = (
        f'<a href="{esc(v["status_url"])}">Villa {vnum}</a>' if linked else f"Villa {vnum}"
    )
    technician_cell = (
        esc(v["technician"]) if linked else '<span style="color:var(--muted)">&mdash;</span>'
    )
    row_cls = " is-linked" if linked else "row-muted"
    return f'''<tr class="{row_cls}" data-search="villa {vnum} {esc(status)}">
          <td class="villa-id">{villa_id_cell}</td>
          <td><span class="badge {badge_cls}">{esc(status)}</span></td>
          <td><div class="progress-cell"><div class="progress-track"><div class="progress-fill{kp_zero}" style="width:{kp_pct}%"></div></div><span class="mono">{v["kp_act"]}/{v["kp_total"]}</span></div></td>
          <td><div class="progress-cell"><div class="progress-track"><div class="progress-fill{task_zero}" style="width:{task_pct}%"></div></div><span class="mono">{v["tasks_pass"]}/{v["tasks_total"]}</span></div></td>
          <td><span class="{issues_cls}">{v["open_issues"]}</span></td>
          <td><span class="rp-dot {rp_cls}"></span>{rp_label}</td>
          <td>{technician_cell}</td>
        </tr>'''


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Apes Hill Villas Fleet</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* Layout concept: a fleet roster -- one row per villa, progress read at a
   glance, status and report-package provenance as separate signals so
   "is it done" and "do we trust the data" never get confused.
   Brand: MNE Innovations -- black/navy, Inter, cyan-to-indigo accent. */
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
a{color:var(--accent-ink);}
h1,h2{text-wrap:balance; margin:0;}
.wrap{max-width:1100px; margin:0 auto; padding-block:0 48px;}

.topbar{
  position:sticky; top:env(safe-area-inset-top,0px); z-index:15;
  background:var(--surface); border-bottom:1px solid var(--line); padding-block:10px;
}
.topbar-inner{max-width:1100px; margin:0 auto; display:flex; align-items:center; gap:14px; flex-wrap:wrap;}
.topbar-brand{display:flex; align-items:center; gap:9px;}
.topbar-brand img{height:22px; width:auto; display:block;}
.topbar-title{font-family:var(--f-display); font-weight:600; font-size:19px; letter-spacing:.02em; white-space:nowrap;}
.search-box{
  display:flex; align-items:center; gap:6px; background:var(--surface-2);
  border:1px solid var(--line); border-radius:7px; padding:6px 10px; min-width:170px; margin-left:auto;
}
.search-box svg{flex:none; opacity:.55;}
.search-box input{border:none; background:transparent; outline:none; color:var(--ink); font-family:var(--f-body); font-size:13.5px; width:100%;}
.search-box input::placeholder{color:var(--muted);}

.hero{padding-block:28px 20px;}
.eyebrow{font-family:var(--f-display); font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent-ink); font-weight:600;}
h1.page-title{font-family:var(--f-display); font-size:42px; font-weight:300; letter-spacing:-.005em; margin-top:4px;}
.hero-sub{color:var(--muted); font-size:14.5px; margin-top:8px; max-width:66ch;}

.kpi-row{display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-block:20px 8px;}
.kpi{
  background:var(--surface); border:1px solid var(--line); border-radius:10px;
  padding:14px 16px; display:flex; flex-direction:column; gap:4px;
}
.kpi-label{font-family:var(--f-display); font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted);}
.kpi-value{font-family:var(--f-mono); font-size:24px; font-weight:500; font-variant-numeric:tabular-nums;}
.kpi-value small{font-size:13px; color:var(--muted); font-weight:400;}

.fleet-bar{
  display:flex; align-items:center; gap:14px; margin-top:18px; background:var(--surface);
  border:1px solid var(--line); border-radius:10px; padding:12px 16px; flex-wrap:wrap;
}
.fleet-bar-track{flex:1 1 280px; height:8px; border-radius:999px; background:var(--surface-2); overflow:hidden; display:flex;}
.fleet-bar-seg{height:100%;}
.fleet-bar-label{font-size:12.5px; color:var(--muted); white-space:nowrap;}
.fleet-legend{display:flex; gap:14px; flex-wrap:wrap; font-size:12px; color:var(--muted);}
.fleet-legend span{display:inline-flex; align-items:center; gap:5px;}
.fleet-legend i{width:9px; height:9px; border-radius:3px; display:inline-block;}

.section{padding-block:30px 8px;}
.section-head{display:flex; align-items:baseline; gap:12px; margin-bottom:14px; flex-wrap:wrap;}
.section-title{font-family:var(--f-display); font-size:22px; font-weight:600;}
.section-sub{font-size:13px; color:var(--muted); margin-left:auto;}

.card{background:var(--surface); border:1px solid var(--line); border-radius:10px; overflow:hidden;}
.table-scroll{overflow-x:auto;}
table{width:100%; border-collapse:collapse; font-size:13.5px;}
thead th{
  text-align:left; font-family:var(--f-display); font-size:11px; letter-spacing:.07em; text-transform:uppercase;
  color:var(--muted); padding:10px 16px; border-bottom:1px solid var(--line); background:var(--surface-2);
}
tbody td{padding:12px 16px; border-bottom:1px solid var(--line); vertical-align:middle;}
tbody tr:last-child td{border-bottom:none;}
tbody tr.is-linked{cursor:pointer;}
tbody tr.is-linked:hover td{background:var(--surface-2);}
.villa-id{font-family:var(--f-display); font-size:16px; font-weight:600;}
.villa-id a{color:var(--ink); text-decoration:none;}
.villa-id a:hover{color:var(--accent-ink);}
.mono{font-family:var(--f-mono); font-variant-numeric:tabular-nums;}
.progress-cell{display:flex; align-items:center; gap:8px; white-space:nowrap;}
.progress-track{width:72px; height:6px; border-radius:999px; background:var(--surface-2); overflow:hidden;}
.progress-fill{height:100%; background:var(--accent); border-radius:999px;}
.progress-fill.zero{background:var(--line);}

.badge{
  display:inline-flex; align-items:center; gap:5px; font-family:var(--f-display); font-size:11.5px;
  letter-spacing:.03em; font-weight:600; padding:3px 9px; border-radius:999px; white-space:nowrap;
}
.b-pass{background:var(--pass-bg); color:var(--pass);}
.b-pend{background:var(--pend-bg); color:var(--pend);}
.b-nr{background:var(--nr-bg); color:var(--nr);}
.rp-dot{width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:6px; vertical-align:middle;}
.rp-done{background:var(--pass);}
.rp-pending{background:var(--nr);}
.issues-count{font-family:var(--f-mono); font-variant-numeric:tabular-nums;}
.issues-count.has-issues{color:var(--pend);}
.row-muted td{color:var(--muted);}
.row-muted .villa-id a{color:var(--muted);}

footer{padding-block:30px 10px; font-size:12.5px; color:var(--muted); border-top:1px solid var(--line); margin-top:10px;}
footer a{color:var(--muted); text-decoration:underline;}

@media (max-width:760px){
  .kpi-row{grid-template-columns:repeat(2,1fr);}
  h1.page-title{font-size:32px;}
  thead th:nth-child(5), tbody td:nth-child(5){display:none;}
}
</style>
</head>
<body>


<div class="topbar">
  <div class="topbar-inner">
    <div class="topbar-brand"><img src="assets/logo.png" alt="MNE Innovations"><div class="topbar-title">Apes Hill Hilltop Villas</div></div>
    <div class="search-box">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
      <input id="filter" type="search" placeholder="Find a villa&hellip;" aria-label="Filter villas">
    </div>
  </div>
</div>

<div class="wrap">
  <section class="hero">
    <div class="eyebrow">Apes Hill Hilltop Villas &middot; St. James, Barbados</div>
    <h1 class="page-title">HomeWorks Takeover &mdash; Fleet Status</h1>
    <p class="hero-sub">Live commissioning status across all 14 villas. Click a villa to open its pages; the Report Package column tracks which villas have had a Lutron Designer report processed for engravings and fixture data &mdash; the rest are running on tracker data alone until their report arrives.</p>

    <div class="kpi-row">
      <div class="kpi"><div class="kpi-label">Villas</div><div class="kpi-value">__TOTAL_VILLAS__</div></div>
      <div class="kpi"><div class="kpi-label">Complete</div><div class="kpi-value">__COMPLETE__<small>/__TOTAL_VILLAS__</small></div></div>
      <div class="kpi"><div class="kpi-label">In progress</div><div class="kpi-value">__INPROGRESS__<small>/__TOTAL_VILLAS__</small></div></div>
      <div class="kpi"><div class="kpi-label">Not started</div><div class="kpi-value">__NOTSTARTED__<small>/__TOTAL_VILLAS__</small></div></div>
      <div class="kpi"><div class="kpi-label">Keypads live</div><div class="kpi-value">__KP_LIVE__<small>/__KP_TOTAL__</small></div></div>
      <div class="kpi"><div class="kpi-label">Open issues</div><div class="kpi-value">__OPEN_ISSUES__</div></div>
    </div>

    <div class="fleet-bar">
      <span class="fleet-bar-label">Fleet progress</span>
      <div class="fleet-bar-track">
        <div class="fleet-bar-seg" style="width:__PCT_COMPLETE__%; background:var(--pass);"></div>
        <div class="fleet-bar-seg" style="width:__PCT_INPROGRESS__%; background:var(--pend);"></div>
        <div class="fleet-bar-seg" style="width:__PCT_NOTSTARTED__%; background:var(--line);"></div>
      </div>
      <div class="fleet-legend">
        <span><i style="background:var(--pass)"></i>Complete (__COMPLETE__)</span>
        <span><i style="background:var(--pend)"></i>In progress (__INPROGRESS__)</span>
        <span><i style="background:var(--line)"></i>Not started (__NOTSTARTED__)</span>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-head">
      <h2 class="section-title">Villas</h2>
      <span class="section-sub">Sorted by parcel order &middot; Villa 1 and 13 do not exist in this project</span>
    </div>
    <div class="card table-scroll">
      <table id="fleet-table">
        <thead>
          <tr><th>Villa</th><th>Status</th><th>Keypads</th><th>Checklist</th><th>Open issues</th><th>Report package</th><th>Technician</th></tr>
        </thead>
        <tbody>
__TABLE_ROWS__
        </tbody>
      </table>
    </div>
  </section>

  <footer>
    Source: Apes Hill Hilltop Villas Master Commissioning Tracker &mdash; "Dashboard" and "Villa Tracker" tabs. Regenerated by the Update Site workflow.
    Only Villa 15 has a processed Lutron Designer report package so far; its engravings and fixture-level detail come from that report rather than the tracker alone.
  </footer>
</div>

<script>
(function(){
  var input = document.getElementById('filter');
  var rows = Array.prototype.slice.call(document.querySelectorAll('#fleet-table tbody tr'));
  input.addEventListener('input', function(){
    var q = input.value.trim().toLowerCase();
    rows.forEach(function(r){
      var match = q.length === 0 || r.textContent.toLowerCase().indexOf(q) !== -1;
      r.style.display = match ? '' : 'none';
    });
  });
  rows.forEach(function(r){
    if (r.classList.contains('is-linked')){
      r.addEventListener('click', function(ev){
        if (ev.target.closest('a')) return;
        var a = r.querySelector('.villa-id a');
        if (a) window.location.href = a.href;
      });
    }
  });
})();
</script>

</body>
</html>
"""


def main():
    computed = json.load(open(DATA_DIR / "villas_summary.json"))
    by_vnum = {v["vnum"]: v for v in computed}
    by_vnum[VILLA15["vnum"]] = VILLA15
    for vnum in NOT_STARTED_VNUMS:
        by_vnum[vnum] = {
            "vnum": vnum, "status": "Not Started",
            "kp_act": 0, "kp_total": 26,
            "tasks_pass": 0, "tasks_total": 23,
            "open_issues": 0, "total_issues": 0,
            "technician": "—", "report_package": "pending",
            "status_url": "",
        }

    rows = [by_vnum[v] for v in PARCEL_ORDER]
    table_rows = "\n".join(render_row(v) for v in rows)

    total = len(rows)
    complete = sum(1 for v in rows if v["status"] == "Complete")
    in_progress = sum(1 for v in rows if v["status"] == "In Progress")
    not_started = sum(1 for v in rows if v["status"] == "Not Started")
    kp_live = sum(v["kp_act"] for v in rows)
    kp_total = sum(v["kp_total"] for v in rows)
    open_issues = sum(v["open_issues"] for v in rows)

    out = TEMPLATE
    out = out.replace("__TABLE_ROWS__", table_rows)
    out = out.replace("__TOTAL_VILLAS__", str(total))
    out = out.replace("__COMPLETE__", str(complete))
    out = out.replace("__INPROGRESS__", str(in_progress))
    out = out.replace("__NOTSTARTED__", str(not_started))
    out = out.replace("__KP_LIVE__", str(kp_live))
    out = out.replace("__KP_TOTAL__", str(kp_total))
    out = out.replace("__OPEN_ISSUES__", str(open_issues))
    out = out.replace("__PCT_COMPLETE__", f"{100 * complete / total:.1f}")
    out = out.replace("__PCT_INPROGRESS__", f"{100 * in_progress / total:.1f}")
    out = out.replace("__PCT_NOTSTARTED__", f"{100 * not_started / total:.1f}")

    fname = SITE_DIR / "index.html"
    fname.write_text(out, encoding="utf-8")
    print("wrote", fname)


if __name__ == "__main__":
    main()
