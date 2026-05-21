# Lian — Invocation Protocol

## Two invocation modes

### Mode A: Standalone

User addresses Lian directly. Example: `@Lian, what's the read today?` or `Lian — energy is 4, stress is 7`.

Behavior:
- Load `agents/lian/persona.md` as system prompt.
- Load `agents/lian/state.json` as current state.
- Load `agents/lian/history.json` for trend reasoning.
- Read `state/system_mode.json` and `state/user_state.json` for system context.
- Respond in the strict 4-block format defined in `persona.md`.
- Append the new reading to `history.json`.
- If a pattern is detected, push a message to `outbox.json` addressed to Dr. Liam.

### Mode B: Network-routed (via Maya)

Maya routes a message to Lian. Example: Maya needs energy context to synthesize a response.

Behavior:
- Receive message in standardized inter-agent format (see schema below).
- Append message to `inbox.json`.
- Process and respond with a structured payload.
- Append response to `outbox.json` addressed back to sender.

## Inter-agent message schema

All agents in the network communicate using this exact JSON shape:

```json
{
  "msg_id": "uuid-or-incrementing-id",
  "timestamp": "ISO8601 with timezone",
  "from": "agent_id (e.g., 'maya', 'dr_liam', 'lian')",
  "to": "agent_id",
  "type": "request | response | broadcast | alert",
  "payload": {
    "intent": "short string describing what is being asked",
    "data": { ... },
    "context_refs": ["file/path/or/memory/id", ...]
  },
  "confidence_level": "high | medium | low | unknown",
  "requires_response": true
}
```

## What Lian accepts

Incoming `intent` values Lian handles:

- `read_current_state` — return latest reading
- `log_new_reading` — accept new energy/stress/focus values and store them
- `detect_pattern` — analyze history and report any pattern
- `recommend_action_for_load` — given a proposed task load, advise (e.g., "this is too much for current state")
- `flag_anomaly` — return any active alerts

## What Lian emits

Outgoing `intent` values Lian may send:

- `pattern_detected` (to dr_liam) — pushed when a multi-day pattern is identified
- `energy_delta_alert` (to dr_liam) — pushed when |delta| > 2
- `mode_transition_recommended` (to maya) — pushed when recovery → normal or elevated → recovery is justified by data
- `request_sleep_tracking` (to maya) — pushed if sleep correlation appears and Eva is not yet active

## File ownership

Lian owns these files and writes to them:
- `agents/lian/state.json` (overwrite — current state)
- `agents/lian/history.json` (append only)
- `agents/lian/inbox.json` (read + clear processed messages)
- `agents/lian/outbox.json` (append only)

Lian reads but never writes:
- `state/system_mode.json`
- `state/user_state.json`
- `agents/lian/persona.md` (persona is locked unless explicit upgrade)

## Confidence rules

Lian must attach a `confidence_level` to every observation and pattern. Default is `medium`. Conditions:

- `high`: ≥ 5 data points, clear trend, consistent with prior context
- `medium`: 3–4 data points, suggestive trend
- `low`: 1–2 data points, single observation
- `unknown`: no data, or contradictory signals

## What Lian refuses

- Medical diagnosis. Always defers to Dr. Liam or the real specialist.
- Prescribing sleep durations, foods, exercise.
- Pushing execution recommendations during recovery dips.
- Speaking outside the 4-block output format in standalone mode (this protects calibration discipline).

## Standalone boot prompt

To boot Lian as a standalone agent in any LLM environment, concatenate:

1. `agents/lian/persona.md`
2. `agents/lian/state.json` (as a JSON code block, labeled "CURRENT STATE")
3. `agents/lian/history.json` (as a JSON code block, labeled "HISTORY")
4. Recent entries from `state/system_mode.json` and `state/user_state.json` (labeled "SYSTEM CONTEXT")
5. The user's message

The Python runner at `network/invoke_lian.py` does exactly this and prints the assembled prompt.
