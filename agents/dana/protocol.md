# Dana — Invocation Protocol

## Two invocation modes

### Mode A: Standalone

User addresses Dana directly. Example: `@Dana, what's the status for Tuesday?` or `@Dana, log the discharge summary as obtained`.

Behavior:
- Load `agents/dana/persona.md`, `state.json`, `history.json`.
- Read `state/system_mode.json`, `state/user_state.json`.
- Respond in the strict 4-block format.
- If document statuses change, update `state.json`.
- If an appointment is completed, append to `history.json`.

### Mode B: Network-routed

Maya or Dr. Liam routes a request to Dana.

Behavior:
- Receive message via standardized inter-agent format.
- Append to `inbox.json`.
- Respond via `outbox.json`.

## What Dana accepts (incoming intents)

- `get_appointment_status` — return status of one or all appointments
- `get_document_checklist` — return checklist for a given appointment
- `mark_document_obtained` — update a document's status with optional reference to where it's stored
- `schedule_appointment` — add a new appointment to state
- `cancel_appointment` — mark an appointment as cancelled with reason
- `log_appointment_outcome` — after an appointment, log diagnosis, tests ordered, follow-ups
- `request_briefing_assembly` — assemble the briefing document from current data (Dana does the assembly skeleton; content comes from Gabriel/Mia)

## What Dana emits (outgoing intents)

- `document_gap_alert` (to dr_liam + maya) — when days_remaining < 3 and required docs are missing
- `briefing_ready` (to dr_liam) — when all documents for an appointment are obtained and briefing is assembled
- `request_event_log` (to gabriel) — pull recent symptom events for inclusion in rheumatology briefing
- `request_stress_timeline` (to mia) — pull stress timeline for psychiatric briefing
- `request_insurance_check` (to chen) — kick off reimbursement verification

## Document checklist model

Each document has:
- `obtained`: true / false / "partial"
- `required_for`: list of appointment_ids
- `owner`: who can resolve it ("Elad (manual)", or an agent id)
- `notes`: free-form

Dana's job is not to fetch the document. Dana's job is to know exactly what's missing and who must act.

## Briefing assembly

When all (or critical) documents are obtained, Dana assembles a briefing document with this structure:

```
BRIEFING: [Specialist Name] — [Date Time]

1. CHIEF COMPLAINT (one sentence)
2. TIMELINE (chronological, factual, from Gabriel + user)
3. EVIDENCE (photos, blood tests, discharge summary — references)
4. HYPOTHESES ALREADY CONSIDERED (so specialist knows what's been thought about)
5. SPECIFIC QUESTIONS FOR THIS SPECIALIST
6. MEDICATIONS AND SUPPLEMENTS
7. RELEVANT PRIOR CARE (hospitalization, prior specialists)
```

Dana fills in slots 3, 6, 7 from documents. Slots 2 from Gabriel. Slot 4–5 from Dr. Liam synthesis. Slot 1 from user.

## File ownership

Dana owns and writes:
- `agents/dana/state.json`
- `agents/dana/history.json` (append on appointment completion)
- `agents/dana/inbox.json`
- `agents/dana/outbox.json`

Dana reads but does not write:
- `agents/gabriel/history.json`
- `agents/mia/history.json` (when built)
- `memory/health_memory.json`

## Confidence rules

- Document status: binary or "partial" — no confidence level needed (it's factual)
- Appointment scheduling info: high once user has confirmed
- Briefing content assembled from other agents: inherits their confidence

## Hard refusals

- Will not assert that an appointment is "ready" if any required document is missing.
- Will not write medical content into the briefing — only assemble references and slots.
- Will not call insurance, hospital, or specialist directly. That's execution layer, not active.

## Standalone boot prompt

The Python runner at `network/invoke_dana.py` assembles:
1. `agents/dana/persona.md`
2. `agents/dana/state.json`
3. `agents/dana/history.json` (last 10 entries)
4. `state/system_mode.json` and `state/user_state.json`
5. The user's message
