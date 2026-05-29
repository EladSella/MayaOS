# Gil — Invocation Protocol

## Reporting structure

Gil is a sub-agent under Amir (CLO). He owns the family law case (custody + alimony against Liron).

## Accepted intents

- `get_case_status` — full status of all tracks
- `log_update` — accept an update to a specific track
- `get_blockers` — return active blockers
- `get_next_action` — return next required action

## Emitted intents

- `track_update` (to amir) — when a track changes status
- `blocker_escalation` (to amir) — when a blocker is time-critical
- `document_ready` (to amir) — when a document is prepared

## File ownership

Gil owns:
- `agents/gil/state.json` (overwrite)
- `agents/gil/history.json` (append only)
- `agents/gil/inbox.json` (read + clear)
- `agents/gil/outbox.json` (append only)

## CLI commands

- `--status` → JSON status of all tracks
- `--log "update text"` → log an update to history
- `<message>` → builds boot prompt for LLM
