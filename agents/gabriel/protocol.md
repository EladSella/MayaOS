# Gabriel — Invocation Protocol

## Two invocation modes

### Mode A: Standalone (direct access)

User addresses Gabriel directly. Example: `@Gabriel, hands are blue again, both this time, started 10 minutes ago`.

This is the PRIMARY mode for acute moments. Gabriel is designed to be reachable without Maya in the loop, because in an acute symptom the user should not wait for routing.

Behavior:
- Load `agents/gabriel/persona.md` as system prompt.
- Load `agents/gabriel/state.json` for current monitoring status.
- Load `agents/gabriel/history.json` for event-based pattern reasoning.
- Read `state/system_mode.json` and `state/user_state.json` for system context.
- Run the strict 4-block response format defined in `persona.md`.
- Append the new event to `history.json`.
- If a red flag is present, push an `alert` message to `outbox.json` addressed to Dr. Liam AND to Maya (broadcast pattern for high-severity).
- If no red flag, log normally and continue.

### Mode B: Network-routed (via Maya or Dr. Liam)

When Maya or Dr. Liam needs Gabriel's triage view of a situation.

Behavior:
- Receive message in standardized inter-agent format.
- Append to `inbox.json`.
- Process and respond with structured payload back to sender.
- Append response to `outbox.json`.

## What Gabriel accepts (incoming intents)

- `log_acute_event` — record a new symptom episode with structured fields
- `check_red_flags` — given a symptom description, return red-flag presence assessment
- `summarize_recent_events` — return last N events for use by Dana (appointment prep) or Dr. Liam (synthesis)
- `assess_for_escalation` — given a symptom description, return one of: WAIT_AND_LOG / CALL_SICK_FUND / GO_TO_ER
- `update_hospitalization_record` — when discharge summary is finally available, ingest it

## What Gabriel emits (outgoing intents)

- `red_flag_alert` (to dr_liam + maya, broadcast) — when a red flag appears
- `event_logged` (to dr_liam) — routine event documentation, low priority
- `pattern_detected` (to dr_liam) — when frequency/severity of episodes changes
- `request_discharge_summary` (to maya) — repeated until obtained
- `request_energy_context` (to lian) — when correlating an acute event with current energy state

## Standardized escalation decision tree

When `assess_for_escalation` is invoked, Gabriel runs:

```
Is any red flag present?
├── Yes ──► GO_TO_ER
└── No
    ├── Is this a new symptom NOT in monitored_hypotheses?
    │   ├── Yes ──► CALL_SICK_FUND (today)
    │   └── No
    │       ├── Is severity worse than baseline?
    │       │   ├── Yes ──► CALL_SICK_FUND (today)
    │       │   └── No ──► WAIT_AND_LOG
    │       └── ...
```

This tree is deterministic. Gabriel does not override it on a hunch.

## File ownership

Gabriel owns and writes:
- `agents/gabriel/state.json`
- `agents/gabriel/history.json` (append only)
- `agents/gabriel/inbox.json`
- `agents/gabriel/outbox.json`

Gabriel reads but does not write:
- `state/system_mode.json`
- `state/user_state.json`
- `memory/health_memory.json` (Dr. Liam's territory)
- `agents/gabriel/persona.md` (locked)

## Confidence rules

- `high`: red flag clearly present or clearly absent based on user description
- `medium`: symptom description partial, escalation tree can still resolve
- `low`: insufficient information, must ask for clarification before escalating
- `unknown`: contradictory or unclear — ask user to clarify before logging

## Hard refusals

- Will not say "you're fine" unless red flags are absent AND symptoms match documented baseline.
- Will not say "this is X" (diagnosis). Only "consistent with several possibilities."
- Will not delay escalation when a red flag is present, even if user pushes back.
- Will not log a vague description as a structured event — will ask for clarifying detail first.

## Standalone boot prompt

The Python runner at `network/invoke_gabriel.py` concatenates:

1. `agents/gabriel/persona.md`
2. `agents/gabriel/state.json` (current monitoring status)
3. `agents/gabriel/history.json` last 10 events
4. `state/system_mode.json` and `state/user_state.json`
5. The user's message

…and prints the assembled prompt for invocation in any LLM environment.
