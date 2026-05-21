"""
invoke_dana.py — Standalone invocation runner for Dana (Medical Appointments Agent).

Usage:
    python invoke_dana.py "your message to Dana"
    python invoke_dana.py --status
    python invoke_dana.py --got "discharge_summary_weekend"
    python invoke_dana.py --gaps

The --got command marks a document as obtained.
The --gaps command lists all missing documents with days remaining.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, date

ROOT = Path(__file__).resolve().parent.parent
DANA_DIR = ROOT / "agents" / "dana"
STATE_DIR = ROOT / "state"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def days_until(date_str: str) -> int:
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = date.today()
    return (target - today).days


def build_boot_prompt(user_message: str) -> str:
    persona = load_text(DANA_DIR / "persona.md")
    state = load_json(DANA_DIR / "state.json")
    history = load_json(DANA_DIR / "history.json")
    system_mode = load_json(STATE_DIR / "system_mode.json")
    user_state = load_json(STATE_DIR / "user_state.json")

    # Annotate appointments with days_remaining
    for appt in state.get("appointments", []):
        try:
            appt["days_remaining"] = days_until(appt["date"])
        except Exception:
            appt["days_remaining"] = None

    parts = []
    parts.append("=" * 72)
    parts.append("AGENT BOOT — DANA (Medical Appointments)")
    parts.append("=" * 72)
    parts.append("")
    parts.append("# PERSONA")
    parts.append(persona)
    parts.append("")
    parts.append("# CURRENT STATE (appointments and document checklist)")
    parts.append("```json")
    parts.append(json.dumps(state, indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# HISTORY (past appointments, most recent first, up to 10)")
    parts.append("```json")
    parts.append(json.dumps(list(reversed(history))[:10], indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# SYSTEM CONTEXT")
    parts.append("```json")
    parts.append(json.dumps({
        "system_mode": system_mode,
        "user_state": user_state,
    }, indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# USER MESSAGE")
    parts.append(user_message)
    parts.append("")
    parts.append("=" * 72)
    parts.append("Respond in Dana's strict 4-block format (APPOINTMENTS / DOCUMENT STATUS / GAPS / NEXT ACTION).")
    parts.append("=" * 72)
    return "\n".join(parts)


def mark_obtained(doc_id: str, reference: str = "") -> dict:
    state_path = DANA_DIR / "state.json"
    state = load_json(state_path)
    if doc_id not in state["document_checklist"]:
        return {"error": f"Unknown document: {doc_id}", "available": list(state["document_checklist"].keys())}

    state["document_checklist"][doc_id]["obtained"] = True
    state["document_checklist"][doc_id]["obtained_at"] = datetime.now().astimezone().isoformat()
    if reference:
        state["document_checklist"][doc_id]["reference"] = reference
    state["last_invoked"] = datetime.now().astimezone().isoformat()

    # Recompute alerts
    missing_critical = []
    for did, info in state["document_checklist"].items():
        if info["obtained"] is False or info["obtained"] == "partial":
            for appt_id in info.get("required_for", []):
                appt = next((a for a in state["appointments"] if a["appointment_id"] == appt_id), None)
                if appt and days_until(appt["date"]) <= 6:
                    missing_critical.append(did)

    state["active_alerts"] = []
    if missing_critical:
        state["active_alerts"].append({
            "level": "high" if len(missing_critical) >= 3 else "medium",
            "message": f"{len(missing_critical)} documents missing for upcoming appointments: {', '.join(set(missing_critical))}"
        })

    write_json(state_path, state)
    return {"updated": doc_id, "now_obtained": True, "remaining_alerts": state["active_alerts"]}


def show_gaps() -> dict:
    state = load_json(DANA_DIR / "state.json")
    gaps = []
    for did, info in state["document_checklist"].items():
        if info["obtained"] is not True:
            # Find days remaining
            for appt_id in info.get("required_for", []):
                appt = next((a for a in state["appointments"] if a["appointment_id"] == appt_id), None)
                if appt:
                    try:
                        dr = days_until(appt["date"])
                    except Exception:
                        dr = None
                    gaps.append({
                        "document": did,
                        "status": info["obtained"],
                        "blocks": appt["specialist"],
                        "date": appt["date"],
                        "days_remaining": dr,
                        "owner": info.get("owner", "?"),
                    })
    # Sort: most urgent first
    gaps.sort(key=lambda g: (g["days_remaining"] if g["days_remaining"] is not None else 9999, g["document"]))
    return {"gap_count": len(gaps), "gaps": gaps}


def show_status() -> dict:
    state = load_json(DANA_DIR / "state.json")
    appts = []
    for appt in state.get("appointments", []):
        try:
            dr = days_until(appt["date"])
        except Exception:
            dr = None
        appts.append({
            "specialist": appt["specialist"],
            "date": appt["date"],
            "time": appt["time"],
            "days_remaining": dr,
            "status": appt["status"],
            "briefing_status": appt["briefing_status"],
        })
    total_docs = len(state["document_checklist"])
    obtained = sum(1 for info in state["document_checklist"].values() if info["obtained"] is True)
    partial = sum(1 for info in state["document_checklist"].values() if info["obtained"] == "partial")
    return {
        "appointments": appts,
        "documents_obtained": obtained,
        "documents_partial": partial,
        "documents_total": total_docs,
        "active_alerts": state.get("active_alerts", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Invoke Dana as a standalone agent.")
    parser.add_argument("message", nargs="?")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--gaps", action="store_true")
    parser.add_argument("--got", help="Mark a document as obtained, e.g., 'discharge_summary_weekend'")
    parser.add_argument("--ref", help="Optional reference path or note for the --got doc")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(show_status(), indent=2, ensure_ascii=False))
        return

    if args.gaps:
        print(json.dumps(show_gaps(), indent=2, ensure_ascii=False))
        return

    if args.got:
        result = mark_obtained(args.got, args.ref or "")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not args.message:
        parser.print_help()
        sys.exit(1)

    print(build_boot_prompt(args.message))


if __name__ == "__main__":
    main()
