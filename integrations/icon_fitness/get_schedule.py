"""
Icon Fitness Schedule Fetcher (Mock)
====================================
Returns the daily schedule for Icon Fitness Hod Hasharon.
Since the real schedule is locked behind the app/login, this
provides a realistic mock for Leo to use.
"""

import json
import argparse
from datetime import datetime

def get_schedule(day: str) -> dict:
    # In a real scenario, this would use Playwright or an API call with state.json
    
    # Mock data based on typical gym schedules
    schedule = {
        "gym": "Icon Fitness Hod Hasharon",
        "date": day if day != "Today" else datetime.now().strftime("%Y-%m-%d"),
        "classes": [
            {"time": "08:00", "name": "Body Pump", "instructor": "Ron", "capacity": 20, "registered": 15, "available_spots": 5},
            {"time": "17:00", "name": "Spinning", "instructor": "Dana", "capacity": 30, "registered": 18, "available_spots": 12},
            {"time": "18:00", "name": "Pilates", "instructor": "Maya", "capacity": 15, "registered": 13, "available_spots": 2},
            {"time": "19:00", "name": "Yoga", "instructor": "Shir", "capacity": 20, "registered": 12, "available_spots": 8},
            {"time": "20:00", "name": "Pilates", "instructor": "Maya", "capacity": 15, "registered": 15, "available_spots": 0}
        ]
    }
    
    return schedule

def main():
    parser = argparse.ArgumentParser(description="Fetch Icon Fitness Schedule")
    parser.add_argument("--day", default="Today", help="Day to fetch schedule for")
    args = parser.parse_args()

    result = get_schedule(args.day)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
