"""
invoke_gabriel.py - Standalone runner for Gabriel (Emergency Health Agent).

Usage:
    python invoke_gabriel.py "your message"
    python invoke_gabriel.py --log "symptom=x side=y duration=z"
    python invoke_gabriel.py --status
    python invoke_gabriel.py --check "symptom description (English or Hebrew)"
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
GABRIEL_DIR = ROOT / "agents" / "gabriel"
STATE_DIR = ROOT / "state"


def load_text(path):
    return path.read_text(encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


RED_FLAG_KEYWORDS = [
    ("severe pain", "Severe pain"),
    ("strong pain", "Severe pain"),
    ("chest pain", "Chest pain"),
    ("shortness of breath", "Shortness of breath"),
    ("can't breathe", "Shortness of breath"),
    ("difficulty breathing", "Shortness of breath"),
    ("loss of sensation", "Loss of sensation"),
    ("no sensation", "Loss of sensation"),
    ("numb", "Loss of sensation"),
    ("significant weakness", "Significant weakness"),
    ("severe weakness", "Significant weakness"),
    ("black finger", "Black fingers / skin breakdown"),
    ("black fingers", "Black fingers / skin breakdown"),
    ("skin breakdown", "Black fingers / skin breakdown"),
    ("open sore", "Black fingers / skin breakdown"),
    ("doesn't return", "Color does not return within 2 hours"),
    ("didn't return", "Color does not return within 2 hours"),
    ("did not return", "Color does not return within 2 hours"),
    ("more than 2 hour", "Color does not return within 2 hours"),
    ("over 2 hour", "Color does not return within 2 hours"),
    ("כאב חזק", "Severe pain"),
    ("כאב חד", "Severe pain"),
    ("כאב עז", "Severe pain"),
    ("כאב חמור", "Severe pain"),
    ("כאב בחזה", "Chest pain"),
    ("לחץ בחזה", "Chest pain"),
    ("קוצר נשימה", "Shortness of breath"),
    ("קושי לנשום", "Shortness of breath"),
    ("לא יכול לנשום", "Shortness of breath"),
    ("קשה לנשום", "Shortness of breath"),
    ("אובדן תחושה", "Loss of sensation"),
    ("חוסר תחושה", "Loss of sensation"),
    ("אין תחושה", "Loss of sensation"),
    ("חולשה חזקה", "Significant weakness"),
    ("חולשה קשה", "Significant weakness"),
    ("חולשה משמעותית", "Significant weakness"),
    ("אצבעות שחורות", "Black fingers / skin breakdown"),
    ("אצבע שחורה", "Black fingers / skin breakdown"),
    ("פצע פתוח", "Black fingers / skin breakdown"),
    ("כיב", "Black fingers / skin breakdown"),
    ("הצבע לא חוזר", "Color does not return within 2 hours"),
    ("לא חזר לצבע", "Color does not return within 2 hours"),
    ("הצבע לא חזר", "Color does not return within 2 hours"),
    ("יותר משעתיים", "Color does not return within 2 hours"),
    ("מעל שעתיים", "Color does not return within 2 hours"),
    ("יותר מ-2 שעות", "Color does not return within 2 hours"),
]


def check_red_flags(description):
    desc = description.lower()
    matched = []
    canonical = set()
    for kw, name in RED_FLAG_KEYWORDS:
        if kw in desc:
            matched.append(kw)
            canonical.add(name)
    return {
        "red_flag_keywords_matched": matched,
        "canonical_red_flags": sorted(canonical),
        "automated_assessment": "GO_TO_ER" if matched else "WAIT_AND_LOG_OR_CALL_SICK_FUND",
        "language_support": ["English", "Hebrew"],
        "caveat": "Keyword pre-screen only. Gabriel must still run the full escalation tree on the actual symptom narrative.",
    }


def slugify(s):
    out = []
    for ch in s:
        if ch == " " or ch == "/":
            out.append("_")
        else:
            out.append(ch)
    return "".join(out)


def build_boot_prompt(user_message):
    persona = load_text(GABRIEL_DIR / "persona.md")
    state = load_json(GABRIEL_DIR / "state.json")
    history = load_json(GABRIEL_DIR / "history.json")
    system_mode = load_json(STATE_DIR / "system_mode.json")
    user_state = load_json(STATE_DIR / "user_state.json")

    parts = []
    parts.append("=" * 72)
    parts.append("AGENT BOOT - GABRIEL (Emergency Health / Triage)")
    parts.append("=" * 72)
    parts.append("")
    parts.append("# PERSONA")
    parts.append(persona)
    parts.append("")
    parts.append("# CURRENT MONITORING STATE")
    parts.append("```json")
    parts.append(json.dumps(state, indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# EVENT HISTORY (most recent first, up to 10)")
    parts.append("```json")
    parts.append(json.dumps(list(reversed(history))[:10], indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# SYSTEM CONTEXT")
    parts.append("```json")
    parts.append(json.dumps({"system_mode": system_mode, "user_state": user_state}, indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# USER MESSAGE")
    parts.append(user_message)
    parts.append("")
    parts.append("=" * 72)
    parts.append("Respond in Gabriel's strict 4-block format (EVENT LOG / RED FLAG CHECK / INTERPRETATION / NEXT ACTION).")
    parts.append("If any red flag is present, surface it explicitly and recommend ER without softening.")
    parts.append("=" * 72)
    return "\n".join(parts)


def log_event(event_str):
    fields = {}
    for token in event_str.split():
        if "=" in token:
            k, v = token.split("=", 1)
            fields[k.strip()] = v.strip().replace("_", " ")

    timestamp = datetime.now().astimezone().isoformat()
    raw_symptom = fields.get("symptom", "unspecified")[:30]
    symptom_slug = slugify(raw_symptom)
    event = {
        "event_id": "evt_" + timestamp[:10].replace("-", "_") + "_" + symptom_slug,
        "timestamp": timestamp,
        "event_type": fields.get("event_type", "symptom_episode"),
        "symptom_summary": fields.get("symptom", "Unspecified - see notes"),
        "duration": fields.get("duration", "Unknown"),
        "side": fields.get("side", "n/a"),
        "red_flags_present_at_time": [],
        "outcome": fields.get("outcome", "Logged. Awaiting follow-up."),
        "documentation_source": "invoke_gabriel.py --log",
        "confidence_level": fields.get("confidence", "medium"),
        "notes": fields.get("notes", ""),
    }

    history_path = GABRIEL_DIR / "history.json"
    history = load_json(history_path)
    history.append(event)
    write_json(history_path, history)

    state_path = GABRIEL_DIR / "state.json"
    state = load_json(state_path)
    state["last_invoked"] = timestamp
    state["current_status"]["last_episode_timestamp"] = timestamp
    state["current_status"]["last_episode_summary"] = event["symptom_summary"]
    write_json(state_path, state)

    return event


def show_status():
    state = load_json(GABRIEL_DIR / "state.json")
    history = load_json(GABRIEL_DIR / "history.json")
    return json.dumps({
        "monitoring_mode": state["current_status"]["monitoring_mode"],
        "active_acute_event": state["current_status"]["active_acute_event"],
        "active_red_flags": state["current_status"]["active_red_flags"],
        "last_episode": {
            "timestamp": state["current_status"]["last_episode_timestamp"],
            "summary": state["current_status"]["last_episode_summary"],
        },
        "hospitalization_summary_obtained": state["hospitalization"]["discharge_summary_obtained"],
        "history_count": len(history),
        "active_alerts": state.get("active_alerts", []),
    }, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Invoke Gabriel as a standalone agent.")
    parser.add_argument("message", nargs="?")
    parser.add_argument("--log")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--check")
    args = parser.parse_args()

    if args.status:
        print(show_status())
        return
    if args.log:
        event = log_event(args.log)
        print("Event logged:")
        print(json.dumps(event, indent=2, ensure_ascii=False))
        return
    if args.check:
        print(json.dumps(check_red_flags(args.check), indent=2, ensure_ascii=False))
        return
    if not args.message:
        parser.print_help()
        sys.exit(1)
    print(build_boot_prompt(args.message))


if __name__ == "__main__":
    main()
