"""
invoke_leo.py — Standalone invocation runner for Leo (Healthy Lifestyle Agent).

Usage:
    python invoke_leo.py "your message to Leo"
    python invoke_leo.py --log "sleep=7.5 workout=running nutrition=8"
    python invoke_leo.py --status
"""

import json
import sys
import argparse
import random
from datetime import datetime
from pathlib import Path
from core import AgentRunner

def log_reading(runner: AgentRunner, reading_str: str) -> dict:
    fields = {}
    for token in reading_str.split():
        if "=" in token:
            k, v = token.split("=", 1)
            try:
                fields[k.strip()] = float(v.strip())
            except ValueError:
                fields[k.strip()] = v.strip()

    timestamp = datetime.now().astimezone().isoformat()
    entry = {
        "timestamp": timestamp,
        "sleep": fields.get("sleep"),
        "workout": fields.get("workout"),
        "nutrition": fields.get("nutrition"),
        "meditation": fields.get("meditation"),
        "context": "Logged via invoke_leo.py --log",
    }

    runner.update_history(entry)

    state = runner.load_json(runner.agent_dir / "state.json")
    state["last_invoked"] = timestamp
    if entry.get("sleep"):
        state["metrics"]["sleep_hours_avg"] = entry["sleep"]
    if entry.get("workout"):
        state["metrics"]["workouts_this_week"] += 1
    if entry.get("nutrition"):
        state["metrics"]["nutrition_score"] = entry["nutrition"]
    if entry.get("meditation") == "done":
        state["daily_meditation"]["completed_today"] = True
        state["metrics"]["meditation_streak"] += 1
        
    runner.update_state(state)
    return entry

def show_status(runner: AgentRunner) -> str:
    state = runner.load_json(runner.agent_dir / "state.json")
    history = runner.load_json(runner.agent_dir / "history.json")
    return json.dumps({
        "metrics": state["metrics"],
        "meditation": state["daily_meditation"],
        "history_count": len(history),
        "last_invoked": state.get("last_invoked"),
    }, indent=2, ensure_ascii=False)

def run_icon_registration(class_name: str, day: str, time: str) -> dict:
    import subprocess
    import json
    integration_path = Path(__file__).resolve().parent.parent / "integrations" / "icon_fitness" / "register.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(integration_path), "--class-name", class_name, "--day", day, "--time", time],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        out = e.stdout.strip() if e.stdout else ""
        err = e.stderr.strip() if e.stderr else ""
        msg = err if err else out
        try:
            # If the integration passed JSON despite exiting with error code 1
            return json.loads(msg)
        except:
            return {"status": "error", "message": f"Integration failed: {msg}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_icon_schedule(day: str) -> dict:
    import subprocess
    import json
    integration_path = Path(__file__).resolve().parent.parent / "integrations" / "icon_fitness" / "get_schedule.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(integration_path), "--day", day],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Failed to fetch schedule: {e.stderr}"}

def main():
    parser = argparse.ArgumentParser(description="Invoke Leo as a standalone agent.")
    parser.add_argument("message", nargs="?", help="Message to Leo.")
    parser.add_argument("--log", help="Quick reading log, e.g., 'sleep=7.5 workout=running nutrition=8'")
    parser.add_argument("--status", action="store_true", help="Show Leo's current state.")
    parser.add_argument("--register", nargs=3, metavar=("CLASS", "DAY", "TIME"), help="Register for an Icon Fitness class")
    parser.add_argument("--schedule", nargs="?", const="Today", help="Fetch Icon Fitness schedule for a given day (defaults to Today)")
    args = parser.parse_args()

    runner = AgentRunner("leo", "Healthy Lifestyle")

    if args.status:
        print(show_status(runner))
        return

    if args.log:
        entry = log_reading(runner, args.log)
        print("Logged:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return

    if args.register:
        cls_name, day, time = args.register
        result = run_icon_registration(cls_name, day, time)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.schedule:
        result = run_icon_schedule(args.schedule)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if not args.message:
        parser.print_help()
        sys.exit(1)

    # Get dynamic meditation
    med_title = "5 Minute Guided Meditation"
    med_url = "https://www.youtube.com/watch?v=inpok4MKVLM"
    try:
        med_path = Path(__file__).resolve().parent.parent / "integrations" / "youtube" / "get_meditation.py"
        res = subprocess.run([sys.executable, str(med_path)], capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        if data.get("status") == "success":
            med_title = data.get("title")
            med_url = data.get("url")
    except:
        pass
    
    # Automatically fetch Pilates schedule for today
    schedule_data = run_icon_schedule("Today")
    pilates_classes = [c for c in schedule_data.get("classes", []) if "Pilates" in c["name"]]
    
    schedule_text = ["# UPCOMING PILATES CLASSES (ICON FITNESS HOD HASHARON)"]
    if pilates_classes:
        for c in pilates_classes[:2]: # Show the next 2 classes
            schedule_text.append(f"- {c['time']} with {c['instructor']} | Registered: {c['registered']}/{c['capacity']} | Available spots: {c['available_spots']}")
    else:
        schedule_text.append("- No Pilates classes available today.")
    
    custom_blocks = [
        "# RANDOM MEDITATION OF THE DAY (Must use this link!)",
        f"Title: {med_title}",
        f"URL: {med_url}",
        "",
        *schedule_text
    ]

    prompt = runner.build_boot_prompt(args.message, custom_blocks)
    print(prompt)

if __name__ == "__main__":
    main()
