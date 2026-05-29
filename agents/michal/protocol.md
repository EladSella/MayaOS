# Michal — Invocation Protocol

## Reporting structure

Michal is a sub-agent under Amir (CLO). She owns the IDF trauma recognition claim.

## Accepted intents

- `get_case_status` — full status of all tracks
- `log_update` — accept an update (e.g., opinion received)
- `get_blockers` — return active blockers
- `get_next_action` — return next required action

## Emitted intents

- `track_update` (to amir) — when a track changes status
- `opinion_received` (to amir) — when psychiatric opinion arrives
- `request_health_context` (to dr_liam) — when health records needed for documentation

## File ownership

Michal owns:
- `agents/michal/state.json` (overwrite)
- `agents/michal/history.json` (append only)
- `agents/michal/inbox.json` (read + clear)
- `agents/michal/outbox.json` (append only)

## CLI commands

- `--status` → JSON status of all tracks
- `--log "update text"` → log an update to history
- `<message>` → builds boot prompt for LLM
