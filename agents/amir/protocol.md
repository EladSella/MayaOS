# Amir — Invocation Protocol

## Reporting structure

Amir is Tier 1 in the Legal division, directly under Maya (CEO). He synthesizes Gil (family case) and Michal (IDF case).

## Two invocation modes

### Mode A: Standalone

User addresses Amir directly. Example: `@Amir, מה המצב המשפטי?`

Behavior:
- Load `agents/amir/persona.md` as system prompt.
- Load `agents/amir/state.json` as current state.
- Load `agents/amir/history.json` for context.
- Load `agents/gil/state.json` (Gil's case status).
- Load `agents/michal/state.json` (Michal's case status).
- Respond in the strict format defined in persona.md.
- If a blocker becomes critical, push to `outbox.json` addressed to Maya.

### Mode B: Network-routed (via Maya)

Maya routes a message to Amir for legal synthesis.

Behavior:
- Receive message in `inbox.json`.
- Process and respond via `outbox.json`.

## Inter-agent message schema

```json
{
  "msg_id": "uuid",
  "timestamp": "ISO8601",
  "from": "amir | gil | michal | maya",
  "to": "amir | maya",
  "type": "request | response | broadcast | alert",
  "payload": {
    "intent": "string",
    "data": {},
    "context_refs": []
  },
  "confidence_level": "high | medium | low | unknown",
  "requires_response": true
}
```

## Accepted intents

- `get_case_summary` — return status of both cases
- `get_blockers` — return active blockers
- `get_next_actions` — return prioritized action list
- `log_update` — accept a case update and store to history
- `flag_escalation` — flag an issue that needs Maya's attention

## Emitted intents

- `case_blocker_critical` (to maya) — when a blocker becomes time-sensitive
- `synthesis_ready` (to maya) — after requested synthesis
- `request_health_context` (to dr_liam) — when trauma documentation needed for Michal

## File ownership

Amir owns:
- `agents/amir/state.json` (overwrite — current synthesis)
- `agents/amir/history.json` (append only)
- `agents/amir/inbox.json` (read + clear)
- `agents/amir/outbox.json` (append only)

Amir reads:
- `agents/gil/state.json`
- `agents/michal/state.json`
- `agents/amir/persona.md` (locked)

## CLI commands

- `--status` → JSON synthesis of both cases, blockers, next actions
- `--synthesize` → full synthesis prompt (for LLM)
- `<message>` → builds boot prompt including both sub-agent states
