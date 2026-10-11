"""
invoke_leo.py — Standalone runner for Leo (Lifestyle Agent).

Usage:
  python invoke_leo.py "your message"
  python invoke_leo.py --status
  python invoke_leo.py --log "workout=pilates duration=60"
  python invoke_leo.py --schedule [--day Today] [--filter פילאטיס]
  python invoke_leo.py --register --class-name "פילאטיס" --time "18:00" [--day Today] [--dry-run]
  python invoke_leo.py --inbox
  python invoke_leo.py --send <to> <intent> <json_data>
  python invoke_leo.py --process-inbox
"""

import json
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from core import AgentRunner, MessageBus

AGENT_ID = "leo"
ROLE_TITLE = "Lifestyle Agent"

# Path to Icon Fitness integration scripts
ICON_FITNESS_DIR = Path(__file__).resolve().parent.parent / "integrations" / "icon_fitness"


def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    icon = state.get("icon_fitness", {})
    return json.dumps({
        "agent": AGENT_ID,
        "system_mode": state.get("system_mode"),
        "last_invoked": state.get("last_invoked"),
        "active_blockers": state.get("active_blockers", []),
        "metrics": state.get("metrics", {}),
        "icon_fitness": {
            "session_valid": icon.get("session_valid"),
            "last_registration": icon.get("last_registration"),
            "registrations_this_week": icon.get("registrations_this_week", []),
        }
    }, indent=2, ensure_ascii=False)


def show_schedule(day: str, class_filter: str = None):
    """Fetch and display the Icon Fitness class schedule."""
    script = ICON_FITNESS_DIR / "get_schedule.py"
    if not script.exists():
        print(json.dumps({"status": "error", "message": f"Schedule script not found at {script}"}))
        return

    cmd = [sys.executable, str(script), "--day", day]
    if class_filter:
        cmd += ["--filter", class_filter]

    print(f"🏋️  Leo → Fetching Icon Fitness schedule for: {day}" + (f" (filter: {class_filter})" if class_filter else ""))
    print("─" * 50)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ICON_FITNESS_DIR))
        output = result.stdout.strip()
        if output:
            data = json.loads(output)

            if data.get("status") == "session_missing":
                print("⚠️  SESSION MISSING")
                print(f"   {data['message']}")
                print(f"\n   👉 Run: {data['action_required']}")
                return

            if data.get("status") == "session_expired":
                print("⚠️  SESSION EXPIRED")
                print(f"   {data['message']}")
                print(f"\n   👉 Run: {data['action_required']}")
                return

            if data.get("status") == "error":
                print(f"❌ Error: {data.get('message')}")
                return

            # Pretty-print the schedule
            print(f"📅  {data.get('gym', 'Icon Fitness')} — {data.get('date', day)}")
            classes = data.get("classes", [])
            if not classes:
                print("   No classes found for this day/filter.")
            else:
                print(f"   Found {data.get('classes_found', len(classes))} class(es):\n")
                for i, cls in enumerate(classes, 1):
                    raw = cls.get("raw_text", "")
                    time_val = cls.get("time", "")
                    if time_val:
                        print(f"   {i}. [{time_val}] {raw}")
                    else:
                        print(f"   {i}. {raw}")
        else:
            if result.stderr:
                print(f"❌ Error: {result.stderr.strip()}")
            else:
                print("⚠️  No output from schedule fetcher.")
    except json.JSONDecodeError:
        print(result.stdout)
    except Exception as e:
        print(f"❌ Failed to run schedule fetcher: {e}")


def register_class(class_name: str, time_str: str, day: str, dry_run: bool, runner: AgentRunner):
    """Register for a class and update Leo's state."""
    script = ICON_FITNESS_DIR / "register.py"
    if not script.exists():
        print(json.dumps({"status": "error", "message": f"Register script not found at {script}"}))
        return

    print(f"🏋️  Leo → {'[DRY RUN] ' if dry_run else ''}Registering for: {class_name} at {time_str} on {day}")
    print("─" * 50)

    cmd = [
        sys.executable, str(script),
        "--class-name", class_name,
        "--day", day,
        "--time", time_str,
    ]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ICON_FITNESS_DIR))
        output = result.stdout.strip()

        if output:
            data = json.loads(output)
        else:
            data = {"status": "error", "message": result.stderr.strip() or "No output"}

        status = data.get("status", "error")

        if status in ("session_missing", "session_expired"):
            print(f"⚠️  {status.upper().replace('_', ' ')}")
            print(f"   {data['message']}")
            print(f"\n   👉 Run: {data['action_required']}")
            return

        if status == "success":
            print(f"✅  REGISTERED!")
            print(f"   Class: {data.get('class_name')}")
            print(f"   Date:  {data.get('date')} at {data.get('time')}")
            print(f"   Gym:   {data.get('gym')}")
            if data.get("screenshot"):
                print(f"   📸 Screenshot: {data['screenshot']}")

            # Update Leo's state
            state_path = runner.agent_dir / "state.json"
            state = runner.load_json(state_path)
            if "icon_fitness" not in state:
                state["icon_fitness"] = {}
            state["icon_fitness"]["last_registration"] = {
                "class_name": class_name,
                "date": data.get("date"),
                "time": time_str,
                "timestamp": datetime.now().isoformat()
            }
            regs = state["icon_fitness"].get("registrations_this_week", [])
            regs.append({
                "class_name": class_name,
                "date": data.get("date"),
                "time": time_str,
                "registered_at": datetime.now().isoformat()
            })
            state["icon_fitness"]["registrations_this_week"] = regs[-10:]  # keep last 10
            state["icon_fitness"]["session_valid"] = True

            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print("   📊 Leo state updated.")

            # Append to history
            history_path = runner.agent_dir / "history.json"
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
            history.append({
                "timestamp": datetime.now().isoformat(),
                "event": "icon_fitness_registration",
                "class_name": class_name,
                "date": data.get("date"),
                "time": time_str,
                "status": "success"
            })
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

        elif status == "dry_run_success":
            print(f"🔍  DRY RUN — Class found!")
            print(f"   {data.get('message')}")
            print(f"   Register button: '{data.get('register_button_found')}'")
            if data.get("screenshot"):
                print(f"   📸 Screenshot: {data['screenshot']}")

        elif status == "class_not_found":
            print(f"⚠️  CLASS NOT FOUND")
            print(f"   {data.get('message')}")
            if data.get("matching_text_found"):
                print(f"   Partial matches: {data['matching_text_found'][:3]}")
            print(f"\n   💡 {data.get('suggestion', '')}")
            if data.get("screenshot"):
                print(f"   📸 Screenshot saved: {data['screenshot']}")

        else:
            print(f"❌ {status.upper()}: {data.get('message')}")

    except json.JSONDecodeError:
        print(result.stdout)
    except Exception as e:
        print(f"❌ Failed to run registration: {e}")


def log_workout(log_str: str, runner: AgentRunner):
    """Quick log of a workout to state and history."""
    state_path = runner.agent_dir / "state.json"
    state = runner.load_json(state_path)
    metrics = state.get("metrics", {})
    metrics["workouts_this_week"] = metrics.get("workouts_this_week", 0) + 1
    state["metrics"] = metrics
    state["last_invoked"] = datetime.now().isoformat()

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    history_path = runner.agent_dir / "history.json"
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = []
    history.append({
        "timestamp": datetime.now().isoformat(),
        "event": "workout_log",
        "data": log_str
    })
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "agent": AGENT_ID,
        "status": "logged",
        "data": log_str,
        "workouts_this_week": metrics["workouts_this_week"]
    }, ensure_ascii=False, indent=2))


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
    parser.add_argument("--log", metavar="DATA", help="Log a workout/meal/sleep entry.")
    # Icon Fitness flags
    parser.add_argument("--schedule", action="store_true", help="Fetch Icon Fitness class schedule.")
    parser.add_argument("--day", default="Today", help="Day for schedule/register (Today, Tomorrow, Monday...)")
    parser.add_argument("--filter", dest="class_filter", default=None,
                        help="Filter schedule by class name (e.g. 'פילאטיס')")
    parser.add_argument("--register", action="store_true", help="Register for a class at Icon Fitness.")
    parser.add_argument("--class-name", dest="class_name", default="פילאטיס",
                        help="Class name to register for (default: פילאטיס)")
    parser.add_argument("--time", dest="time_str", default=None,
                        help="Class time HH:MM (required with --register)")
    parser.add_argument("--dry-run", action="store_true",
                        help="With --register: find class but don't actually book")
    # Messaging flags
    parser.add_argument("--inbox", action="store_true", help="Show unread inbox messages")
    parser.add_argument("--send", nargs=3, metavar=("TO", "INTENT", "DATA"),
                        help="Send message: --send <to> <intent> <json_data>")
    parser.add_argument("--process-inbox", action="store_true", help="Process all inbox messages")

    args = parser.parse_args()

    runner = AgentRunner(AGENT_ID, ROLE_TITLE)
    bus = MessageBus()

    # ── Messaging ───────────────────────────────────────────────────────────
    if args.inbox:
        show_inbox(bus)
        return

    if args.send:
        send_message(bus, args.send[0], args.send[1], args.send[2])
        return

    if args.process_inbox:
        process_inbox(bus)
        return

    # ── Status ──────────────────────────────────────────────────────────────
    if args.status:
        print(show_status(runner))
        return

    # ── Log ─────────────────────────────────────────────────────────────────
    if args.log:
        log_workout(args.log, runner)
        return

    # ── Icon Fitness: Schedule ───────────────────────────────────────────────
    if args.schedule:
        show_schedule(args.day, args.class_filter)
        return

    # ── Icon Fitness: Register ───────────────────────────────────────────────
    if args.register:
        if not args.time_str:
            print("❌ --register requires --time HH:MM  (e.g. --time 18:00)")
            sys.exit(1)
        register_class(args.class_name, args.time_str, args.day, args.dry_run, runner)
        return

    # ── LLM Boot Prompt ─────────────────────────────────────────────────────
    if args.message:
        prompt = runner.build_boot_prompt(args.message)
        print(prompt)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
