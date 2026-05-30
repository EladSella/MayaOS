"""
cowork.py — MayaOS Inter-Agent Message Router

Usage:
  python network/cowork.py send <from> <to> <intent> [--data '{"key":"val"}']
  python network/cowork.py inbox <agent>
  python network/cowork.py status <agent>
  python network/cowork.py broadcast <from> <intent> --division <div>
  python network/cowork.py log [--last N]
  python network/cowork.py tree
"""

import json
import sys
import uuid
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
NETWORK = ROOT / "network"
AGENTS = ROOT / "agents"
HIERARCHY_FILE = NETWORK / "hierarchy.json"
MESSAGE_LOG = NETWORK / "message_log.json"
MESSAGE_SCHEMA = NETWORK / "message_schema.json"


# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════

def load_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def agent_dir(agent: str) -> Path:
    return AGENTS / agent.lower()


def inbox_path(agent: str) -> Path:
    return agent_dir(agent) / "inbox.json"


def outbox_path(agent: str) -> Path:
    return agent_dir(agent) / "outbox.json"


def state_path(agent: str) -> Path:
    return agent_dir(agent) / "state.json"


# ══════════════════════════════════════════
# HIERARCHY
# ══════════════════════════════════════════

def load_hierarchy() -> dict:
    return load_json(HIERARCHY_FILE)


def can_message(from_agent: str, to_agent: str) -> tuple[bool, str]:
    """Returns (allowed, reason)."""
    h = load_hierarchy()
    f = from_agent.lower()
    t = to_agent.lower()

    if f not in h:
        return False, f"סוכן לא מוכר: {f}"
    if t not in h:
        return False, f"סוכן לא מוכר: {t}"

    fnode = h[f]
    tnode = h[t]

    # CEO can message anyone
    if fnode["tier"] == 0:
        return True, "CEO — גישה מלאה"

    # UP: reports_to
    if fnode.get("reports_to") == t:
        return True, f"דיווח UP: {f} → {t}"

    # DOWN: direct_reports
    if t in fnode.get("direct_reports", []):
        return True, f"הנחיה DOWN: {f} → {t}"

    # CROSS: cross_links
    if t in fnode.get("cross_links", []):
        return True, f"קשר רוחבי CROSS: {f} ↔ {t}"

    # Anyone can message CEO (maya)
    if tnode["tier"] == 0:
        return True, "הודעה ל-CEO מותרת לכולם"

    return False, f"אסור: {f} לא יכול לפנות ישירות ל-{t} (אין קשר מוגדר)"


def get_division_agents(division: str) -> list:
    h = load_hierarchy()
    return [name for name, node in h.items() if node.get("division") == division]


# ══════════════════════════════════════════
# MESSAGING
# ══════════════════════════════════════════

def build_message(from_agent: str, to_agent: str, intent: str,
                  data: dict, msg_type: str = "request",
                  requires_response: bool = False) -> dict:
    return {
        "msg_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "from": from_agent.lower(),
        "to": to_agent.lower(),
        "type": msg_type,
        "payload": {
            "intent": intent,
            "data": data,
            "context_refs": []
        },
        "confidence_level": "high",
        "requires_response": requires_response,
        "status": "unread"
    }


def deliver(msg: dict):
    """Write message to target's inbox.json."""
    target = msg["to"]
    ipath = inbox_path(target)
    if not ipath.parent.exists():
        raise FileNotFoundError(f"תיקיית סוכן לא קיימת: {ipath.parent}")
    inbox = load_json(ipath) if ipath.exists() else []
    if not isinstance(inbox, list):
        inbox = []
    inbox.append(msg)
    save_json(ipath, inbox)


def log_message(msg: dict, status: str = "delivered"):
    log = load_json(MESSAGE_LOG) if MESSAGE_LOG.exists() else []
    if not isinstance(log, list):
        log = []
    log.append({
        "msg_id": msg["msg_id"],
        "timestamp": msg["timestamp"],
        "from": msg["from"],
        "to": msg["to"],
        "intent": msg["payload"]["intent"],
        "status": status
    })
    save_json(MESSAGE_LOG, log)


# ══════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════

def cmd_send(args):
    from_a, to_a, intent = args.from_agent, args.to, args.intent
    data = {}
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            data = {"text": args.data}

    allowed, reason = can_message(from_a, to_a)
    if not allowed:
        print(json.dumps({"error": reason}, ensure_ascii=False, indent=2))
        sys.exit(1)

    msg = build_message(from_a, to_a, intent, data,
                        requires_response=args.requires_response)
    deliver(msg)
    log_message(msg, "delivered")

    print(json.dumps({
        "status": "delivered",
        "msg_id": msg["msg_id"],
        "from": from_a,
        "to": to_a,
        "intent": intent,
        "permission": reason
    }, ensure_ascii=False, indent=2))


def cmd_inbox(args):
    agent = args.agent.lower()
    ipath = inbox_path(agent)
    if not ipath.exists():
        print(json.dumps({"agent": agent, "inbox": [], "unread": 0}, ensure_ascii=False, indent=2))
        return
    inbox = load_json(ipath)
    if not isinstance(inbox, list):
        inbox = []
    unread = [m for m in inbox if m.get("status") == "unread"]

    if args.unread_only:
        print(json.dumps({
            "agent": agent,
            "unread": len(unread),
            "messages": unread
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "agent": agent,
            "total": len(inbox),
            "unread": len(unread),
            "messages": inbox[-20:]  # last 20
        }, ensure_ascii=False, indent=2))


def cmd_status(args):
    agent = args.agent.lower()
    h = load_hierarchy()
    node = h.get(agent, {})
    sp = state_path(agent)
    state = load_json(sp) if sp.exists() else {}
    ipath = inbox_path(agent)
    inbox = load_json(ipath) if ipath.exists() else []
    if not isinstance(inbox, list):
        inbox = []
    unread = len([m for m in inbox if m.get("status") == "unread"])

    print(json.dumps({
        "agent": agent,
        "tier": node.get("tier"),
        "division": node.get("division"),
        "reports_to": node.get("reports_to"),
        "direct_reports": node.get("direct_reports", []),
        "cross_links": node.get("cross_links", []),
        "inbox_unread": unread,
        "state_snapshot": {k: v for k, v in list(state.items())[:5]}
    }, ensure_ascii=False, indent=2))


def cmd_broadcast(args):
    from_a = args.from_agent.lower()
    intent = args.intent
    data = {}
    if args.data:
        try:
            data = json.loads(args.data)
        except Exception:
            data = {"text": args.data}

    targets = []
    if args.division:
        targets = get_division_agents(args.division)
    elif args.all:
        targets = list(load_hierarchy().keys())
    else:
        print("שגיאה: ציין --division או --all")
        sys.exit(1)

    # Remove self
    targets = [t for t in targets if t != from_a]

    results = []
    for target in targets:
        allowed, reason = can_message(from_a, target)
        if not allowed:
            results.append({"to": target, "status": "skipped", "reason": reason})
            continue
        msg = build_message(from_a, target, intent, data,
                            msg_type="broadcast", requires_response=False)
        deliver(msg)
        log_message(msg, "delivered")
        results.append({"to": target, "status": "delivered", "msg_id": msg["msg_id"]})

    print(json.dumps({
        "broadcast_from": from_a,
        "intent": intent,
        "results": results
    }, ensure_ascii=False, indent=2))


def cmd_log(args):
    log = load_json(MESSAGE_LOG) if MESSAGE_LOG.exists() else []
    if not isinstance(log, list):
        log = []
    n = args.last or 20
    recent = log[-n:]
    print(json.dumps({
        "total_messages": len(log),
        "showing_last": n,
        "log": list(reversed(recent))
    }, ensure_ascii=False, indent=2))


def cmd_tree(args):
    h = load_hierarchy()
    tier0 = [n for n, d in h.items() if d.get("tier") == 0]

    def build_tree(agent, depth=0):
        node = h.get(agent, {})
        ipath = inbox_path(agent)
        inbox = load_json(ipath) if ipath.exists() else []
        unread = len([m for m in (inbox if isinstance(inbox, list) else []) if m.get("status") == "unread"])
        badge = f" [{unread} unread]" if unread else ""
        indent = "  " * depth
        connector = "└─ " if depth > 0 else ""
        print(f"{indent}{connector}{agent.upper()}{badge} ({node.get('division', '')})")
        for child in node.get("direct_reports", []):
            build_tree(child, depth + 1)

    print("\n=== MayaOS Agent Network ===\n")
    for root_agent in tier0:
        build_tree(root_agent)
    print()

    # Cross-links
    print("Cross-division links:")
    for name, node in h.items():
        for cl in node.get("cross_links", []):
            print(f"  {name} ↔ {cl}")
    print()


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MayaOS COWORK — Inter-Agent Message Router"
    )
    sub = parser.add_subparsers(dest="command")

    # send
    p_send = sub.add_parser("send", help="שלח הודעה בין סוכנים")
    p_send.add_argument("from_agent")
    p_send.add_argument("to")
    p_send.add_argument("intent")
    p_send.add_argument("--data", help="JSON data payload", default=None)
    p_send.add_argument("--requires-response", action="store_true", default=False)

    # inbox
    p_inbox = sub.add_parser("inbox", help="הצג inbox של סוכן")
    p_inbox.add_argument("agent")
    p_inbox.add_argument("--unread-only", action="store_true", default=False)

    # status
    p_status = sub.add_parser("status", help="סטטוס מלא של סוכן")
    p_status.add_argument("agent")

    # broadcast
    p_bc = sub.add_parser("broadcast", help="שלח לכל מחלקה")
    p_bc.add_argument("from_agent")
    p_bc.add_argument("intent")
    p_bc.add_argument("--data", default=None)
    p_bc.add_argument("--division", default=None)
    p_bc.add_argument("--all", action="store_true", default=False)

    # log
    p_log = sub.add_parser("log", help="לוג הודעות")
    p_log.add_argument("--last", type=int, default=20)

    # tree
    sub.add_parser("tree", help="עץ סוכנים עם unread count")

    args = parser.parse_args()

    cmd_map = {
        "send": cmd_send,
        "inbox": cmd_inbox,
        "status": cmd_status,
        "broadcast": cmd_broadcast,
        "log": cmd_log,
        "tree": cmd_tree,
    }

    if args.command not in cmd_map:
        parser.print_help()
        sys.exit(1)

    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
