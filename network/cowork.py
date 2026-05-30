"""
cowork.py — MayaOS Inter-Agent Message Router

CLI:
  python cowork.py send <from> <to> <intent> [--data '{"key":"value"}']
  python cowork.py status <agent>
  python cowork.py process <agent>
  python cowork.py broadcast <from> <intent> [--to division|all]
  python cowork.py log [--limit N]
  python cowork.py routes <agent>

COWORK rules:
  UP    — agent → direct superior only
  DOWN  — agent → direct reports only
  CROSS — agent → cross_links only
  BROADCAST — tier-0 (maya) only
  No autonomous loops. Trigger-based only.
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running from network/ directory
sys.path.insert(0, str(Path(__file__).parent))
from core import MessageBus


def cmd_send(args, bus: MessageBus):
    try:
        data = json.loads(args.data) if args.data else {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in --data: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        msg_id = bus.send(
            from_agent=args.FROM,
            to_agent=args.TO,
            intent=args.intent,
            data=data,
            msg_type=args.type,
            confidence=args.confidence,
            requires_response=args.requires_response,
        )
        print(f"✅ Message sent | msg_id: {msg_id} | {args.FROM} → {args.TO} | intent: {args.intent}")
    except PermissionError as e:
        print(f"❌ Routing blocked: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args, bus: MessageBus):
    try:
        status = bus.agent_status(args.agent)
        print(json.dumps(status, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_process(args, bus: MessageBus):
    unread = bus.read_unread(args.agent)
    if not unread:
        print(f"📭 No unread messages for {args.agent}")
        return
    print(f"📬 {len(unread)} unread message(s) or {args.agent}:\n")
    for msg in unread:
        print(f"  [{msg['msg_id']}] {msg['from']} → {msg['to']}")
        print(f"  intent : {msg['payload']['intent']}")
        print(f"  data   : {json.dumps(msg['payload']['data'], ensure_ascii=False)}")
        print(f"  time   : {msg['timestamp']}")
        print()
        bus.mark_read(args.agent, msg["msg_id"])
        bus.update_log_status(msg["msg_id"], "read")
    print(f"✅ Marked {len(unread)} messages as read.")


def cmd_broadcast(args, bus: MessageBus):
    try:
        data = json.loads(args.data) if args.data else {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in --data: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        msg_id = bus.send(from_agent=args.FROM, to_agent="broadcast", intent=args.intent, data=data, msg_type="broadcast")
        print(f"📡 Broadcast sent | msg_id: {msg_id} | from: {args.FROM} | intent: {args.intent}")
    except PermissionError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)


def cmd_log(args, bus: MessageBus):
    entries = bus.get_log(limit=args.limit)
    if not entries:
        print("📋 Message log is empty.")
        return
    print(f"📋 Last {len(entries)} messages (most recent first):\n")
    for e in entries:
        status_icon = {"delivered": "📨", "read": "✅", "responded": "↩️"}.get(e.get("status", ""), "•")
        print(f"  {status_icon} [{e.get('msg_id','?')}] {e.get('from','?')} → {e.get('to','?')}")
        print(f"     intent: {e.get('intent','?')}  |  {e.get('timestamp','?')[:19]}")
        if e.get("summary"):
            print(f"     summary: {e['summary'][:80]}")
        print()


def cmd_routes(args, bus: MessageBus):
    try:
        h_entry = bus.get_hierarchy(args.agent)
        h = json.loads((Path(__file__).parent / "hierarchy.json").read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    print(f"\n📡 Allowed routes for '{args.agent}' (tier {h_entry.get('tier')}, {h_entry.get('division')}):\n")
    if h_entry.get("reports_to"):
        print(f"  ↑ UP    → {h_entry['reports_to']}")
    for dr in h_entry.get("direct_reports", []):
        print(f"  ↓ DOWN  → {dr}")
    for cl in h_entry.get("cross_links", []):
        print(f"  ↔ CROSS → {cl}")
    if h_entry.get("tier") == 0:
        print(f"  📡 BROADCAST → all agents")
    print()


def main():
    parser = argparse.ArgumentParser(description="COWORK — MayaOS Inter-Agent Message Router", formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_send = sub.add_parser("send")
    p_send.add_argument("FROM"); p_send.add_argument("TO"); p_send.add_argument("intent")
    p_send.add_argument("--data", default=None)
    p_send.add_argument("--type", default="request", choices=["request","response","broadcast","alert"])
    p_send.add_argument("--confidence", default="medium", choices=["high","medium","low","unknown"])
    p_send.add_argument("--requires-response", action="store_true")
    p_status = sub.add_parser("status"); p_status.add_argument("agent")
    p_proc = sub.add_parser("process"); p_proc.add_argument("agent")
    p_bc = sub.add_parser("broadcast"); p_bc.add_argument("FTOM"); p_bc.add_argument("intent"); p_bc.add_argument("--data", default=None)
    p_log = sub.add_parser("log"); p_log.add_argument("--limit", type=int, default=20)
    p_routes = sub.add_parser("routes"); p_routes.add_argument("agent")
    args = parser.parse_args()
    bus = MessageBus()
    dispatch = {"send": cmd_send, "status": cmd_status, "process": cmd_process, "broadcast": cmd_broadcast, "log": cmd_log, "routes": cmd_routes}
    dispatch[args.command](args, bus)


if __name__ == "__main__":
    main()
