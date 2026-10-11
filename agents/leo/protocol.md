# Communication Protocol - Leo

## Ownership
- **Owns:** Exercise logs, meal/nutrition logs, sleep duration records, daily meditation routines, and Icon Fitness class registrations.
- **Does NOT Own:** Energy/focus baselines (owned by Lian), Stress/anxiety triggers (owned by Mia), Medical triage/symptoms (owned by Gabriel).

## Interfaces
- **To Lian:** Pulls energy levels to adjust workout intensity.
- **To Mia:** Pushes meditation completion events to help lower tracked stress levels.
- **From Dr. Liam:** Receives high-level directives (e.g., "User recovering from gastroenteritis, enforce bland diet").

## Triggers
- `log_workout`: Updates `workouts_this_week` and pushes to history.
- `log_meal`: Updates `nutrition_score`.
- `log_sleep`: Updates `sleep_hours_avg`.
- `request_meditation`: Dispatches a YouTube link.
- `get_schedule`: Fetches live Icon Fitness Hod HaSharon class schedule via `get_schedule.py`.
- `register_class`: Registers Elad for a class at Icon Fitness via `register.py` (requires active session).

## Icon Fitness Integration
- Session must be established via `setup_session.py` (one-time manual login).
- If session is missing or expired, Leo reports `session_missing` / `session_expired` and instructs the user to re-run `setup_session.py`.
- Registrations are logged to `state.json → icon_fitness.registrations_this_week` and appended to `history.json`.
