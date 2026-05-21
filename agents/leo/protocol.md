# Communication Protocol - Leo

## Ownership
- **Owns:** Exercise logs, meal/nutrition logs, sleep duration records, and daily meditation routines.
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
