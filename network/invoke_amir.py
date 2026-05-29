"""
invoke_amir.py — Standalone runner for Amir (Chief Legal Officer).

Usage:
    python invoke_amir.py "your message to Amir"
    python invoke_amir.py --status
    python invoke_amir.py --synthesize
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from core import AgentRunner

BASE = Path(__file__).parent.parent / "agents"

def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    gil_state = runner.load_json(BASE / "gil" / "state.json")
    michal_state = runner.load_json(BASE / "michal" / "state.json")

    return json.dumps({
        "division": "legal",
        "system_mode": state.get("system_mode"),
        "cases": {
            "family_law": {
                "headline": state["active_cases"]["family_law"]["headline"],
                "stage": state["active_cases"]["family_law"]["stage"],
                "next_date": state["active_cases"]["family_law"]["next_date"],
                "tracks": {
                    "custody_7_7": gil_state["tracks"]["custody_7_7"]["stage"],
                    "alimony": gil_state["tracks"]["alimony_cancellation"]["stage"],
                    "ayala_therapy": gil_state["tracks"]["ayala_therapy"]["stage"],
                },
                "key_agreement": gil_state["key_agreements"][0]["description"] if gil_state.get("key_agreements") else None,
            },
            "idf_claim": {
                "headline": state["active_cases"]["idf_claim"]["headline"],
                "stage": state["active_cases"]["idf_claim"]["stage"],
                "opinion_received": michal_state["tracks"]["expert_opinion"]["opinion_received"],
            }
        },
        "blockers": state.get("active_blockers", []),
        "last_updated": state.get("last_invoked"),
    }, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Invoke Amir — Chief Legal Officer.")
    parser.add_argument("message", nargs="?", help="Message to Amir.")
    parser.add_argument("--status", action="store_true", help="Show synthesis of both cases.")
    parser.add_argument("--synthesize", action="store_true", help="Build full synthesis prompt.")
    args = parser.parse_args()

    runner = AgentRunner("amir", "Chief Legal Officer")

    if args.status:
        print(show_status(runner))
        return

    if args.synthesize or args.message:
        msg = args.message or "סנתז את מצב שתי התביעות הפעילות."
        # Augment boot prompt with sub-agent states
        gil_state = runner.load_json(BASE / "gil" / "state.json")
        michal_state = runner.load_json(BASE / "michal" / "state.json")

        prompt = runner.build_boot_prompt(msg)
        prompt += f"\n\n# GIL STATE (family case)\n```json\n{json.dumps(gil_state, indent=2, ensure_ascii=False)}\n```"
        prompt += f"\n\n# MICHAL STATE (IDF case)\n```json\n{json.dumps(michal_state, indent=2, ensure_ascii=False)}\n```"
        print(prompt)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
