"""
invoke_mia.py — Standalone invocation runner for Mia (Stress Regulation Agent).

Usage:
    python invoke_mia.py "your message to Mia"
    python invoke_mia.py --status
    python invoke_mia.py --log "stressor=lawyer_message intensity=7 somatic=chest_tightness"
    python invoke_mia.py --correlations
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
MIA_DIR = ROOT / "agents" / "mia"
STATE_DIR = ROOT / "state"
MEMORY_DIR = ROOT / "memory"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_boot_prompt(user_message: str) -> str:
    persona = load_text(MIA_DIR / "persona.md")
    state = load_json(MIA_DIR / "state.json")
    history = load_json(MIA_DIR / "history.json")
    system_mode = load_json(STATE_DIR / "system_mode.json")
    user_state = load_json(STATE_DIR / "user_state.json")
    emotional_memory = load_json(MEMORY_DIR / "emotional_memory.json")

    parts = []
    parts.append("=" * 72)
    parts.append("AGENT BOOT — MIA (Stress Regulation)")
    parts.append("=" * 72)
    parts.append("")
    parts.append("# PERSONA")
    parts.append(persona)
    parts.append("")
    parts.append("# CURRENT STATE")
    parts.append("```json")
    parts.append(json.dumps(state, indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# HISTORY (most recent first, up to 10)")
    parts.append("```json")
    parts.append(json.dumps(list(reversed(history))[:10], indent=2, ensure_ascii=False))
    parts.append("```")
    parts.append("")
    parts.append("# EMOTIONAL MEMORY (most recent first, up to 5)")
    parts.append("```json")
    parts.append(json.dumps(list(reversed(emotional_memory))[:5], indent=2, ensure_ascii=False))
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
    parts.append("Respond in Mia's strict 4-block format (OBSERVATION / CORRELATION / PATTERN / NEXT).")
    parts.append("Never use 'just' before a stressor. Never collapse somatic and psychological into one explanation.")
    parts.append("=" * 72)
    return "\n".join(parts)


def log_observation(obs_str: str) -> dict:
    fields = {}
    for token in obs_str.split():
        if "=" in token:
            k, v = token.split("=", 1)
            fields[k.strip()] = v.strip().replace("_", " ")

    timestamp = datetime.now().astimezone().isoformat()
    obs = {
        "timestamp": timestamp,
        "type": fields.get("type", "stress_observation"),
        "stressor": fields.get("stressor", "unspecified"),
        "subjective_intensity": int(fields.get("intensity", 0)) if fields.get("intensity", "").isdigit() else fields.get("intensity"),
        "somatic_component": fields.get("somatic", "none reported"),
        "system_response": fields.get("response", "logged via invoke_mia.py --log"),
        "confidence_level": fields.get("confidence", "medium"),
        "source_ref": "invoke_mia.py --log",
    }

    history_path = MIA_DIR / "history.json"
    history = load_json(history_path)
    history.append(obs)
    write_json(history_path, history)

    state_path = MIA_DIR / "state.json"
    state = load_json(state_path)
    state["last_invoked"] = timestamp
    write_json(state_path, state)

    return obs


def show_correlations() -> dict:
    state = load_json(MIA_DIR / "state.json")
    return {
        "correlations": state.get("correlations_observed", []),
        "interpretation_rule": "confidence: low until 3+ supporting instances, medium at 3-4, high at 5+",
    }


def show_status() -> dict:
    state = load_json(MIA_DIR / "state.json")
    history = load_json(MIA_DIR / "history.json")
    return {
        "current_stress_baseline": state.get("current_stress_baseline"),
        "active_stressors": [
            {
                "id": s["stressor_id"],
                "intensity": s["intensity"],
                "status": s["status"],
            } for s in state.get("active_stressors", [])
        ],
        "correlations_count": len(state.get("correlations_observed", [])),
        "psychiatric_briefing_status": state["psychiatric_briefing_prep"]["briefing_status"],
        "history_count": len(history),
        "active_alerts": state.get("active_alerts", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Invoke Mia as a standalone agent.")
    parser.add_argument("message", nargs="?")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--correlations", action="store_true")
    parser.add_argument("--log", help="Quick stress observation, e.g., 'stressor=x intensity=7 somatic=y'")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(show_status(), indent=2, ensure_ascii=False))
        return

    if args.correlations:
        print(json.dumps(show_correlations(), indent=2, ensure_ascii=False))
        return

    if args.log:
        obs = log_observation(args.log)
        print("Logged:")
        print(json.dumps(obs, indent=2, ensure_ascii=False))
        return

    if not args.message:
        parser.print_help()
        sys.exit(1)

    print(build_boot_prompt(args.message))


if __name__ == "__main__":
    main()
