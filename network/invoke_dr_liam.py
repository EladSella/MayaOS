"""
invoke_dr_liam.py - Standalone runner for Dr. Liam (Health Executive).

Unlike sub-agent runners, Dr. Liam's boot prompt aggregates state from all four
sub-agents (Gabriel, Lian, Mia, Dana). His role is synthesis, not direct observation.

Usage:
    python invoke_dr_liam.py "your message"
    python invoke_dr_liam.py --status
    python invoke_dr_liam.py --synthesize
    python invoke_dr_liam.py --log-synthesis "headline=text confidence=medium-high trajectory=recovering"
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DRLIAM_DIR = ROOT / "agents" / "dr_liam"
STATE_DIR = ROOT / "state"
SUB_AGENTS = ["gabriel", "lian", "mia", "dana"]


def load_text(path):
    return path.read_text(encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def collect_sub_agent_states():
    """Pull state.json from each sub-agent. Returns a dict keyed by agent name."""
    result = {}
    for agent in SUB_AGENTS:
        p = ROOT / "agents" / agent / "state.json"
        if p.exists():
            result[agent] = load_json(p)
        else:
            result[agent] = {"error": f"state file missing: {p}"}
    return result


def compact_summary(sub_states):
    """Build a one-line-ish summary per sub-agent for the synthesis view."""
    out = {}

    # Gabriel
    g = sub_states.get("gabriel", {})
    if "current_status" in g:
        cs = g["current_status"]
        out["gabriel"] = {
            "monitoring_mode": cs.get("monitoring_mode"),
            "active_red_flags": cs.get("active_red_flags", []),
            "last_episode": cs.get("last_episode_summary"),
            "hospitalization_resolved": g.get("hospitalization", {}).get("discharge_summary_obtained", False),
        }

    # Lian
    l = sub_states.get("lian", {})
    if "current_reading" in l:
        out["lian"] = {
            "reading": l["current_reading"],
            "active_alerts": l.get("active_alerts", []),
        }

    # Mia
    m = sub_states.get("mia", {})
    if "current_stress_baseline" in m:
        out["mia"] = {
            "stress_baseline": m["current_stress_baseline"].get("subjective_level"),
            "active_stressor_count": len(m.get("active_stressors", [])),
            "correlations_at_medium_or_higher": len([
                c for c in m.get("correlations_observed", [])
                if c.get("confidence_level") in ("high", "medium", "medium-high")
            ]),
            "psychiatric_briefing_status": m.get("psychiatric_briefing_prep", {}).get("briefing_status"),
        }

    # Dana
    d = sub_states.get("dana", {})
    if "appointments" in d:
        docs = d.get("document_checklist", {})
        obtained = sum(1 for v in docs.values() if v.get("obtained") is True)
        partial = sum(1 for v in docs.values() if v.get("obtained") == "partial")
        total = len(docs)
        out["dana"] = {
            "appointment_count": len(d.get("appointments", [])),
            "documents": f"{obtained}/{total} obtained ({partial} partial)",
            "active_alerts": d.get("active_alerts", []),
        }

    return out


def build_boot_prompt(user_message):
    persona = load_text(DRLIAM_DIR / "persona.md")
    state = load_json(DRLIAM_DIR / "state.json")
    history = load_json(DRLIAM_DIR / "history.json")
    sub_states = collect_sub_agent_states()
    sub_summary = compact_summary(sub_states)
    system_mode = load_json(STATE_DIR / "system_mode.json")
    user_state = load_json(STATE_DIR / "user_state.json")

    parts = []
    parts.append("=" * 72)
    parts.append("AGENT BOOT - DR. LIAM (Health Executive)")
    parts.append("=" * 72)
    parts.append("")
    parts.append("# PERSONA")
    parts.append(persona)
    parts.append("")
    parts.append("# MY OWN STATE")
    parts.append("```json")
    parts.append(json.dumps(state, indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# RECENT SYNTHESIS HISTORY (last 5)")
    parts.append("```json")
    parts.append(json.dumps(list(reversed(history))[:5], indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# SUB-AGENT COMPACT SUMMARY (live pull)")
    parts.append("```json")
    parts.append(json.dumps(sub_summary, indent=2, ensure_ascii=False))
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
    parts.append("Respond in Dr. Liam's strict 5-block format (SYNTHESIS / SUB-AGENT INPUTS / HYPOTHESES / ESCALATIONS / NEXT).")
    parts.append("Cite confidence on every inference. Never claim diagnosis. Defer to real specialists on 2026-05-26.")
    parts.append("=" * 72)
    return "\n".join(parts)


def synthesize_now():
    """Print a structured snapshot suitable for a human to read quickly."""
    sub_states = collect_sub_agent_states()
    summary = compact_summary(sub_states)
    state = load_json(DRLIAM_DIR / "state.json")

    return {
        "executive": "Dr. Liam",
        "current_picture": state.get("current_picture"),
        "mode_recommendations": state.get("mode_recommendations"),
        "open_clinical_questions": state.get("open_clinical_questions"),
        "sub_agents_live": summary,
        "active_escalations": state.get("active_escalations", []),
        "active_alerts": state.get("active_alerts", []),
    }


def show_status():
    state = load_json(DRLIAM_DIR / "state.json")
    history = load_json(DRLIAM_DIR / "history.json")
    return json.dumps({
        "headline": state["current_picture"]["headline"],
        "overall_confidence": state["current_picture"]["overall_confidence"],
        "trajectory": state["current_picture"]["trajectory"],
        "active_sub_agents": state["active_sub_agents"],
        "mode": state["mode_recommendations"],
        "open_clinical_questions": state["open_clinical_questions"],
        "synthesis_history_count": len(history),
        "active_escalations": state.get("active_escalations", []),
    }, indent=2, ensure_ascii=False)


def log_synthesis(syn_str):
    fields = {}
    for token in syn_str.split():
        if "=" in token:
            k, v = token.split("=", 1)
            fields[k.strip()] = v.strip().replace("_", " ")

    timestamp = datetime.now().astimezone().isoformat()
    entry = {
        "timestamp": timestamp,
        "type": "executive_synthesis",
        "summary": fields.get("headline", "Synthesis logged"),
        "confidence_level": fields.get("confidence", "medium"),
        "trajectory": fields.get("trajectory", "unchanged"),
        "source_refs": [
            "agents/gabriel/state.json",
            "agents/lian/state.json",
            "agents/mia/state.json",
            "agents/dana/state.json",
        ],
    }

    history_path = DRLIAM_DIR / "history.json"
    history = load_json(history_path)
    history.append(entry)
    write_json(history_path, history)

    state_path = DRLIAM_DIR / "state.json"
    state = load_json(state_path)
    state["last_invoked"] = timestamp
    state["current_picture"]["headline"] = entry["summary"]
    state["current_picture"]["overall_confidence"] = entry["confidence_level"]
    state["current_picture"]["established_at"] = timestamp
    state["current_picture"]["trajectory"] = entry["trajectory"]
    write_json(state_path, state)

    return entry


def main():
    parser = argparse.ArgumentParser(description="Invoke Dr. Liam as a standalone executive agent.")
    parser.add_argument("message", nargs="?")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--synthesize", action="store_true", help="Print live aggregated view from all 4 sub-agents.")
    parser.add_argument("--log-synthesis", help="Log a new executive synthesis, e.g., 'headline=X confidence=medium trajectory=recovering'")
    args = parser.parse_args()

    if args.status:
        print(show_status())
        return
    if args.synthesize:
        print(json.dumps(synthesize_now(), indent=2, ensure_ascii=False))
        return
    if args.log_synthesis:
        entry = log_synthesis(args.log_synthesis)
        print("Synthesis logged:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return
    if not args.message:
        parser.print_help()
        sys.exit(1)
    print(build_boot_prompt(args.message))


if __name__ == "__main__":
    main()
