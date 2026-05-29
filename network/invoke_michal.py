"""
invoke_michal.py — Standalone runner for Michal (IDF Claim Case Manager).

Usage:
    python invoke_michal.py "your message to Michal"
    python invoke_michal.py --status
    python invoke_michal.py --log "update text"
"""

import json
import sys
import argparse
from datetime import datetime
from core import AgentRunner


def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    return json.dumps({
        "case": state.get("case_name"),
        "tracks": {
            "trauma_recognition": state["tracks"]["trauma_recognition"]["stage"],
            "expert_opinion": {
                "meeting_done": state["tracks"]["expert_opinion"]["psychiatric_meeting"]["completed"],
                "opinion_received": state["tracks"]["expert_opinion"]["opinion_received"],
                "expected": state["tracks"]["expert_opinion"]["expected_date"],
            },
        },
        "blockers": state.get("active_blockers", []),
        "next_court_date": state.get("next_court_date"),
        "last_updated": state.get("last_updated"),
    }, indent=2, ensure_ascii=False)


def log_update(runner: AgentRunner, text: str) -> dict:
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "update": text,
        "logged_by": "invoke_michal.py --log",
    }
    runner.update_history(entry)
    runner.update_state({"last_updated": entry["timestamp"]})
    return entry


def main():
    parser = argparse.ArgumentParser(description="Invoke Michal — IDF Claim Case Manager.")
    parser.add_argument("message", nargs="?", help="Message to Michal.")
    parser.add_argument("--status", action="store_true", help="Show case status.")
    parser.add_argument("--log", help="Log a case update.")
    args = parser.parse_args()

    runner = AgentRunner("michal", "IDF Claim Case Manager")

    if args.status:
        print(show_status(runner))
        return

    if args.log:
        entry = log_update(runner, args.log)
        print("Logged:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return

    if args.message:
        print(runner.build_boot_prompt(args.message))
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
