"""
invoke_lian.py — Standalone invocation runner for Lian (Energy Monitoring Agent).

Usage:
    python invoke_lian.py "your message to Lian"
    python invoke_lian.py --log "energy=6 stress=7 focus=4"
    python invoke_lian.py --status
"""

import json
import sys
import argparse
from datetime import datetime
from core import AgentRunner

def log_reading(runner: AgentRunner, reading_str: str) -> dict:
    """Parse 'energy=6 stress=5 focus=4' style input and append to history."""
    fields = {}
    for token in reading_str.split():
        if "=" in token:
            k, v = token.split("=", 1)
            try:
                fields[k.strip()] = int(v.strip())
            except ValueError:
                fields[k.strip()] = v.strip()

    timestamp = datetime.now().astimezone().isoformat()
    state = runner.load_json(runner.agent_dir / "state.json")
    
    entry = {
        "timestamp": timestamp,
        "energy": fields.get("energy"),
        "stress": fields.get("stress"),
        "focus": fields.get("focus"),
        "burnout_risk": fields.get("burnout_risk"),
        "context": fields.get("context", "Logged via invoke_lian.py --log"),
    }

    runner.update_history(entry)
    
    runner.update_state({
        "last_invoked": timestamp,
        "current_reading": {
            "energy": entry["energy"],
            "stress": entry["stress"],
            "focus": entry["focus"],
            "burnout_risk": entry["burnout_risk"] or state["current_reading"].get("burnout_risk"),
            "source": "invoke_lian.py --log",
        }
    })

    return entry

def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    history = runner.load_json(runner.agent_dir / "history.json")
    return json.dumps({
        "current": state["current_reading"],
        "baseline": state["baseline_reference"],
        "history_count": len(history),
        "last_invoked": state.get("last_invoked"),
        "active_alerts": state.get("active_alerts", []),
    }, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Invoke Lian as a standalone agent.")
    parser.add_argument("message", nargs="?", help="Message to Lian.")
    parser.add_argument("--log", help="Quick reading log, e.g., 'energy=6 stress=5 focus=4'")
    parser.add_argument("--status", action="store_true", help="Show Lian's current state.")
    args = parser.parse_args()

    runner = AgentRunner("lian", "Energy Monitoring")

    if args.status:
        print(show_status(runner))
        return

    if args.log:
        entry = log_reading(runner, args.log)
        print("Logged:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return

    if not args.message:
        parser.print_help()
        sys.exit(1)

    prompt = runner.build_boot_prompt(args.message)
    print(prompt)

if __name__ == "__main__":
    main()
