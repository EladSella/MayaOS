"""
invoke_amir.py — Standalone runner for Amir (Chief Legal Officer).

Usage:
  python invoke_amir.py "your message to Amir"
  python invoke_amir.py --status
  python invoke_amir.py --synthesize
  python invoke_amir.py --inbox
  python invoke_amir.py --send gil track_update '{"note":"עדכון"}'
  python invoke_amir.py --process-inbox
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from core import AgentRunner, MessageBus

BASE = Path(__file__).parent.parent / "agents"
AGENT_ID = "amir"


def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    gil_state = runner.load_json(BASE / "gil" / "state.json")
    michal_state = runner.load_json(BASE / "michal" / "state.json")
    return json.dumps({"division": "legal", "system_mode": state.get("system_mode"), "blockers": state.get("active_blockers", [])}, indent=2, ensure_ascii=False)


def show_inbox(bus): unread = bus.read_unread("amir"); print(json.dumps(unread, indent=2, ensure_ascii=False)) if unread else print("📭 No unread messages for amir")


def send_message(bus, to, intent, data_str):
    try: data = json.loads(data_str) if data_str and data_str != '{}' else {}
    except: data = {"message": data_str}
    try:
        msg_id = bus.send("amir", to, intent, data)
        print(f"✅ Sent | amir → {to} | intent: {intent} | msg_id: {msg_id}")
    except PermissionError as e: print(f"❌ {e}", file=sys.stderr); sys.exit(1)


def process_inbox(bus):
    unread = bus.read_unread("amir")
    if not unread: print("📭 No unread messages for amir"); return
    print(f"📬 Processing {len(unread)} message(s) for amir:\n")
    for msg in unread:
        print(f"  [{msg['msg_id']}] from {msg['from']} | intent: {msg['payload']['intent']}")
        bus.mark_read("amir", msg["msg_id"]); bus.update_log_status(msg["msg_id"], "read")
    print(f"✅ {len(unread)} messages marked as read.")


def main():
    parser = argparse.ArgumentParser(description="Invoke Amir - Chief Legal Officer")
    parser.add_argument("message", nargs="?"); parser.add_argument("--status", action="store_true"); parser.add_argument("--synthesize", action="store_true")
    parser.add_argument("--inbox", action="store_true"); parser.add_argument("--send", nargs=3, metavar=("TMO","INTENT","DATA")); parser.add_argument("--process-inbox", action="store_true")
    args = parser.parse_args()
    runner = AgentRunner("amir", "Chief Legal Officer"); bus = MessageBus()
    if args.inbox: show_inbox(bus); return
    if args.send: send_message(bus, args.send[0], args.send[1], args.send[2]); return
    if args.process_inbox: process_inbox(bus); return
    if args.status: print(show_status(runner)); return
    if args.synthesize or args.message:
        msg = args.message or "ונתז את ם�׮YՑע שפת"
        gil_state = runner.load_json(BASE / "gil" / "state.json"); michal_state = runner.load_json(BASE / "michal" / "state.json")
        prompt = runner.build_boot_prompt(msg)
        prompt += f"\n\n# GIL STATE\n```json\n{json.dumps(gil_state, indent=2, ensure_ascii=False)}\n```"
        prompt += f"\n\n# MICHAL STATE\n```json\n{json.dumps(michal_state, indent=2, ensure_ascii=False)}\n```"
        print(prompt); return
    parser.print_help(); sys.exit(1)


if __name__ == "__main__": main()
