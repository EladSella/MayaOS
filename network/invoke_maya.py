"""
invoke_maya.py — Maya CEO Command Line Interface

Usage:
  python network/invoke_maya.py "יש מייל מד'ר דרואין שצריך תור"
  python network/invoke_maya.py "גיל, מה הסטטוס של תיק לירון?"
  python network/invoke_maya.py "כאב חזה חזק" 
  python network/invoke_maya.py --status
"""

import json
import sys
import uuid
import argparse
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT  = Path(__file__).resolve().parent.parent
NETWORK = ROOT / "network"
AGENTS  = ROOT / "agents"

DIVIDER = "=" * 60

# ══════════════════════════════════════════
# ROUTING RULES — keyword → agent(s)
# ══════════════════════════════════════════
ROUTING_RULES = [
    # EMERGENCY — always first
    {
        "id": "emergency",
        "keywords": ["כאב חזה", "מכחיל", "קוצר נשימה", "לא מגיב", "עלה",
                     "chest pain", "emergency", "אמבולנס", "קריסה", "התעלף"],
        "agents": ["gabriel"],
        "division": "health",
        "priority": "CRITICAL",
        "reason": "מילות מפתח חירום — גבריאל (Triage) מקבל ראשון",
        "also_notify": ["dr_liam"]
    },
    # HEALTH — appointments / Dana
    {
        "id": "appointment",
        "keywords": ["תור", "רופא", "קביעה", "ביקור", "appointment", "clinic",
                     "מרפאה", "מומחה", "בדיקה", "specialist"],
        "agents": ["dana"],
        "division": "health",
        "priority": "routine",
        "reason": "נדרשת קביעת תור — דנה (Appointments) מטפלת",
        "also_notify": ["dr_liam"]
    },
    # HEALTH — stress / Mia
    {
        "id": "stress",
        "keywords": ["סטרס", "לחץ", "חרדה", "מתח", "קשה לי", "לא ישנתי",
                     "stress", "anxiety", "overwhelmed", "burned out"],
        "agents": ["mia"],
        "division": "health",
        "priority": "routine",
        "reason": "מצב רגשי/סטרס — מיה (Stress Regulation) מטפלת",
        "also_notify": ["dr_liam"]
    },
    # HEALTH — energy / Lian
    {
        "id": "energy",
        "keywords": ["אנרגיה", "עייף", "עייפות", "focus", "ריכוז", "energy",
                     "רמת אנרגיה", "לא מרוכז"],
        "agents": ["lian"],
        "division": "health",
        "priority": "routine",
        "reason": "ניטור אנרגיה — ליאן (Energy Monitor) מטפלת",
        "also_notify": []
    },
    # HEALTH — fitness / Leo
    {
        "id": "fitness",
        "keywords": ["אימון", "כושר", "ריצה", "תזונה", "מדיטציה", "gym",
                     "workout", "nutrition", "meditation", "fitness"],
        "agents": ["leo"],
        "division": "health",
        "priority": "routine",
        "reason": "אורח חיים בריא — ליאו (Lifestyle) מטפל",
        "also_notify": []
    },
    # HEALTH — general / Dr. Liam
    {
        "id": "health_general",
        "keywords": ["בריאות", "health", "כאב", "pain", "תסמין", "symptom",
                     "מחלה", "illness", "ד'ר", "דוקטור", "רפואי"],
        "agents": ["dr_liam"],
        "division": "health",
        "priority": "routine",
        "reason": "עניין רפואי — ד'ר ליאם (Health Executive) מטפל",
        "also_notify": []
    },
    # LEGAL — Gil (Liron case)
    {
        "id": "legal_liron",
        "keywords": ["לירון", "משמורת", "מזונות", "איילה", "קסטדי", "7:7",
                     "custody", "alimony", "liron", "תביעה משפחה"],
        "agents": ["gil"],
        "division": "legal",
        "priority": "routine",
        "reason": "תיק משפחה — גיל (Family Case) מטפל",
        "also_notify": ["amir"]
    },
    # LEGAL — Michal (IDF case)
    {
        "id": "legal_idf",
        "keywords": ["צבא", "טראומה", "idf", "army", "מיכל", "תביעה צבאית",
                     "נפגע", "trauma", "ptsd"],
        "agents": ["michal"],
        "division": "legal",
        "priority": "routine",
        "reason": "תיק צבאי — מיכל (IDF Case) מטפלת",
        "also_notify": ["amir"]
    },
    # LEGAL — general / Amir
    {
        "id": "legal_general",
        "keywords": ["משפטי", "legal", "עורך דין", "ברומר", "תביעה", "בית משפט",
                     "דיון", "משפט", "law", "court"],
        "agents": ["amir"],
        "division": "legal",
        "priority": "routine",
        "reason": "עניין משפטי — אמיר (Legal Executive) מטפל",
        "also_notify": []
    },
]

DIVISION_EMOJIS = {
    "health": "🏥",
    "legal": "⚖️",
    "finance": "💰",
    "admin": "📋",
    "ceo": "👑",
    "CRITICAL": "🚨"
}

PRIORITY_COLORS = {
    "CRITICAL": "🚨 CRITICAL",
    "high": "🔴 HIGH",
    "routine": "🟢 ROUTINE",
}

# ══════════════════════════════════════════
# ROUTING ENGINE
# ══════════════════════════════════════════
def analyze_message(text: str) -> list:
    text_lower = text.lower()
    matched = []
    seen_agents = set()

    for rule in ROUTING_RULES:
        for kw in rule["keywords"]:
            if kw.lower() in text_lower:
                agents_new = [a for a in rule["agents"] if a not in seen_agents]
                if agents_new or rule.get("also_notify"):
                    matched.append({**rule, "matched_keyword": kw, "agents": agents_new})
                    seen_agents.update(rule["agents"])
                    seen_agents.update(rule.get("also_notify", []))
                break  # one keyword per rule is enough

    return matched


def load_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def deliver_message(from_a: str, to_a: str, intent: str, data: dict) -> str:
    msg = {
        "msg_id": str(uuid.uuid4()),
        "timestamp": datetime.now().astimezone().isoformat(),
        "from": from_a,
        "to": to_a,
        "type": "request",
        "payload": {"intent": intent, "data": data, "context_refs": []},
        "confidence_level": "high",
        "requires_response": False,
        "status": "unread"
    }
    ipath = AGENTS / to_a / "inbox.json"
    if not ipath.parent.exists():
        return None
    inbox = load_json(ipath) if ipath.exists() else []
    if not isinstance(inbox, list):
        inbox = []
    inbox.append(msg)
    save_json(ipath, inbox)

    # Log
    log_path = NETWORK / "message_log.json"
    log = load_json(log_path) if log_path.exists() else []
    if not isinstance(log, list):
        log = []
    log.append({
        "msg_id": msg["msg_id"],
        "timestamp": msg["timestamp"],
        "from": from_a,
        "to": to_a,
        "intent": intent,
        "status": "delivered"
    })
    save_json(log_path, log)
    return msg["msg_id"]


def agent_display(name: str) -> str:
    display = {
        "maya": "Maya (CEO)",
        "dr_liam": "Dr. Liam (Health Executive)",
        "gabriel": "Gabriel (Emergency Triage)",
        "dana": "Dana (Appointments)",
        "mia": "Mia (Stress Regulation)",
        "lian": "Lian (Energy Monitor)",
        "leo": "Leo (Lifestyle)",
        "amir": "Amir (Legal Executive)",
        "gil": "Gil (Family Case)",
        "michal": "Michal (IDF Case)",
    }
    return display.get(name, name.upper())


# ══════════════════════════════════════════
# MAIN DISPATCH
# ══════════════════════════════════════════
def dispatch(user_message: str):
    print()
    print(DIVIDER)
    print("  MAYA — מנכ\"לית MayaOS")
    print(DIVIDER)
    print(f"  הודעה: {user_message}")
    print(DIVIDER)

    matches = analyze_message(user_message)

    if not matches:
        print()
        print("  מאיה: קיבלתי את ההודעה שלך.")
        print("  לא זיהיתי חלוקה ברורה — אשמור אצלי ואמתין להבהרה.")
        print()
        print("  TIP: נסה לציין:")
        print("    'תור' / 'כאב' / 'לירון' / 'משמורת' / 'בית משפט' / 'מזונות'")
        print(DIVIDER)
        return

    print()
    print("  מאיה: קיבלתי. מנתחת ומנתבת...")
    print()

    all_delivered = []

    for i, match in enumerate(matches, 1):
        div_emoji = DIVISION_EMOJIS.get(match["division"], "📌")
        prio = PRIORITY_COLORS.get(match["priority"], match["priority"])

        print(f"  ── ניתוב {i} ──────────────────────────")
        print(f"  מחלקה   : {div_emoji} {match['division'].upper()}")
        print(f"  עדיפות  : {prio}")
        print(f"  טריגר   : '{match['matched_keyword']}'")
        print(f"  סיבה    : {match['reason']}")
        print()

        # Deliver to primary agents
        for agent in match["agents"]:
            mid = deliver_message("maya", agent, "user_request", {
                "original_message": user_message,
                "routed_by": "maya",
                "reason": match["reason"],
                "priority": match["priority"]
            })
            if mid:
                print(f"  ✅ נשלח ל: {agent_display(agent)}")
                print(f"     msg_id : {mid[:16]}...")
                all_delivered.append((agent, mid))
            else:
                print(f"  ⚠️  {agent_display(agent)} — תיקייה לא קיימת, דלג")

        # Also notify
        for agent in match.get("also_notify", []):
            if agent not in [a for a, _ in all_delivered]:
                mid = deliver_message("maya", agent, "fyi_notification", {
                    "original_message": user_message,
                    "note": f"לידיעה — נשלח ל{match['agents']}",
                    "priority": match["priority"]
                })
                if mid:
                    print(f"  ℹ️  עותק ל: {agent_display(agent)} (לידיעה)")
                    all_delivered.append((agent, mid))
        print()

    print(DIVIDER)
    print(f"  סה\"כ: {len(all_delivered)} סוכנים קיבלו הודעה")
    for agent, mid in all_delivered:
        print(f"    • {agent_display(agent)}")
    print()

    if any(m["priority"] == "CRITICAL" for m in matches):
        print("  ⚠️  MAYA: מצב חירום זוהה — גבריאל ייצור קשר מיידי.")
        print("           אם זו בעיה רפואית פעילה — התקשר לחירום 101.")
    else:
        print("  מאיה: כל הסוכנים הרלוונטיים קיבלו את המשימה.")
        print("        תוכל לפנות ישירות לכל אחד מהם לעדכון.")
    print(DIVIDER)
    print()


def cmd_status():
    """Show Maya's inbox and network overview."""
    print()
    print(DIVIDER)
    print("  MAYA STATUS — סטטוס רשת")
    print(DIVIDER)

    agents_with_dirs = []
    for d in AGENTS.iterdir():
        if d.is_dir():
            ipath = d / "inbox.json"
            inbox = []
            if ipath.exists():
                try:
                    data = load_json(ipath)
                    inbox = data if isinstance(data, list) else []
                except Exception:
                    pass
            unread = len([m for m in inbox if m.get("status") == "unread"])
            agents_with_dirs.append((d.name, unread))

    agents_with_dirs.sort(key=lambda x: -x[1])
    total_unread = sum(u for _, u in agents_with_dirs)

    print(f"  סה\"כ הודעות ממתינות: {total_unread}")
    print()
    for name, unread in agents_with_dirs:
        bar = "🔴" if unread > 2 else "🟡" if unread > 0 else "🟢"
        label = agent_display(name)
        print(f"  {bar} {label:<35} {unread} unread")
    print(DIVIDER)
    print()


# ══════════════════════════════════════════
# ENTRY
# ══════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Maya CEO — MayaOS Command Line")
    parser.add_argument("message", nargs="?", default=None,
                        help="הודעה למאיה בעברית או אנגלית")
    parser.add_argument("--status", action="store_true",
                        help="הצג סטטוס רשת הסוכנים")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.message:
        dispatch(args.message)
    else:
        print()
        print("  MAYA — שורת פקודה")
        print("  דוגמאות:")
        print("    python network/invoke_maya.py \"יש מייל מד'ר דרואין שצריך תור\"")
        print("    python network/invoke_maya.py \"גיל, מה הסטטוס של תיק לירון?\"")
        print("    python network/invoke_maya.py \"כאב חזה חזק\"")
        print("    python network/invoke_maya.py --status")
        print()

if __name__ == "__main__":
    main()
