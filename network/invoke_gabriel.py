"""
invoke_gabriel.py — Standalone runner for Gabriel (Emergency & Triage Agent).

Usage:
  python invoke_gabriel.py "your message"
  python invoke_gabriel.py --status
  python invoke_gabriel.py --inbox
  python invoke_gabriel.py --send <to> <intent> <json_data>
  python invoke_gabriel.py --process-inbox
"""

import json
import sys
import argparse
from pathlib import Path
from core import AgentRunner, MessageBus

AGENT_ID = "gabriel"
ROLE_TITLE = "Emergency & Triage Agent"


def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    return json.dumps({
        "agent": AGENT_ID,
        "system_mode": state.get("system_mode"),
        "last_invoked": state.get("last_invoked"),
        "active_blockers": state.get("active_blockers", []),
    }, indent=2, ensure_ascii=False)


def show_inbox(bus: MessageBus):
    unread = bus.read_unread(AGENT_ID)
    if not unread:
        print(f"📭 No unread messages for {AGENT_ID}")
    else:
        print(json.dumps(unread, indent=2, ensure_ascii=False))


def send_message(bus: MessageBus, to: str, intent: str, data_str: str):
    try:
        data = json.loads(data_str) if data_str and data_str != "{}" else {}
    except json.JSONDecodeError:
        data = {"message": data_str}
    try:
        msg_id = bus.send(AGENT_ID, to, intent, data)
        print(f"✅ Sent | {AGENT_ID} → {to} | intent: {intent} | msg_id: {msg_id}")
    except PermissionError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


def process_inbox(bus: MessageBus):
    unread = bus.read_unread(AGENT_ID)
    if not unread:
        print(f"📭 No unread messages for {AGENT_ID}")
        return
    print(f"📬 Processing {len(unread)} message(s) for {AGENT_ID}:\n")
    for msg in unread:
        print(f"  [{msg['msg_id']}] from {msg['from']} | intent: {msg['payload']['intent']}")
        print(f"  data: {json.dumps(msg['payload']['data'], ensure_ascii=False)}\n")
        bus.mark_read(AGENT_ID, msg["msg_id"])
        bus.update_log_status(msg["msg_id"], "read")
    print(f"✅ {len(unread)} messages marked as read.")


def main():
    parser = argparse.ArgumentParser(description=f"Invoke {AGENT_ID.capitalize()} — {ROLE_TITLE}.")
    parser.add_argument("message", nargs="?", help="Message to agent.")
    parser.add_argument("--status", action="store_true", help="Show agent status.")
    parser.add_argument("--inbox", action="store_true", help="Show unread inbox messages")
    parser.add_argument("--send", nargs=3, metavar=("TO", "INTENT", "DATA"),
                        help="Send message: --send <to> <intent> <json_data>")
    parser.add_argument("--process-inbox", action="store_true", help="Process all inbox messages")
    args = parser.parse_args()

    runner = AgentRunner(AGENT_ID, ROLE_TITLE)
    bus = MessageBus()

    if args.inbox:
        show_inbox(bus)
        return

    if args.send:
        send_message(bus, args.send[0], args.send[1], args.send[2])
        return

    if args.process_inbox:
        process_inbox(bus)
        return

    if args.status:
        print(show_status(runner))
        return

    if args.message:
        prompt = runner.build_boot_prompt(args.message)
        print(prompt)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
