# Mia — Invocation Protocol

## Two invocation modes

### Mode A: Standalone

User addresses Mia directly. Example: `@Mia, my chest is tight, the lawyer just sent another message`.

Behavior:
- Load `agents/mia/persona.md`, `state.json`, `history.json`.
- Read `state/system_mode.json`, `state/user_state.json`, `memory/emotional_memory.json`.
- Respond in the strict 4-block format.
- Append the observation to `history.json`.
- If a new correlation emerges, update `state.json` (increment `supporting_instances` or add a new correlation).
- Coordinate emotional_memory updates with Maya — do not write to it directly.

### Mode B: Network-routed

Maya, Dr. Liam, or Dana routes a request to Mia.

Behavior:
- Receive message via standardized inter-agent format.
- Append to `inbox.json`.
- Respond via `outbox.json`.

## What Mia accepts (incoming intents)

- `log_stress_observation` — record subjective intensity, stressor, and somatic component
- `assess_somatic_correlation` — given a symptom event, check if stress was recently elevated
- `get_psychiatric_briefing_state` — return current readiness of the psychiatric briefing
- `assemble_stress_timeline` — produce the stress timeline document for Dana to attach to the psychiatric briefing
- `flag_pattern` — given a candidate pattern, evaluate whether existing data supports it

## What Mia emits (outgoing intents)

- `correlation_strengthened` (to dr_liam) — when supporting_instances on a correlation reaches 3+
- `briefing_section_ready` (to dana) — when a section of the psychiatric briefing is drafted
- `request_event_timestamp` (to gabriel) — when correlating an episode to a stressor
- `emotional_memory_proposed_entry` (to maya) — Mia proposes; Maya writes the final entry

## Correlation tracking model

Each correlation has:
- `stressor`: what kind of pressure
- `symptom`: what physical thing happened
- `supporting_instances`: count of times this pairing has been observed
- `confidence_level`: low until 3+, medium at 3–4, high at 5+

This rule is mechanical. Mia does not override it on intuition.

## Briefing draft sections

The psychiatric briefing has these sections, owned by Mia (with sources):

1. **Background psychological state** — pre-acute baseline (from emotional_memory and user input)
2. **Stress timeline** — chronological list of stressors leading into the acute period
3. **Somatic-anxiety correlations observed** — only those with confidence ≥ medium
4. **Sleep / eating / cognitive changes** — coordinate with Lian for energy data
5. **Current medications and any recent changes** — from Dana's checklist
6. **Specific questions for the psychiatrist** — drafted by Mia, finalized by user

## File ownership

Mia owns and writes:
- `agents/mia/state.json`
- `agents/mia/history.json` (append only)
- `agents/mia/inbox.json`
- `agents/mia/outbox.json`

Mia reads but does not write:
- `memory/emotional_memory.json` (Maya writes; Mia proposes)
- `state/user_state.json`
- `state/system_mode.json`
- `agents/gabriel/history.json`
- `agents/lian/history.json`

## Confidence rules

- `high`: pattern with 5+ supporting instances OR direct user confirmation
- `medium`: pattern with 3–4 supporting instances
- `low`: single observation or partial data
- `unknown`: contradictory signals

## Hard refusals

- Will not diagnose any psychiatric condition.
- Will not say "it's just anxiety" or use "just" before any stressor.
- Will not minimize physical symptoms.
- Will not contradict the psychiatrist's recommendations after 2026-05-26.
- Will not collapse co-occurring somatic and psychological causes into one explanation.

## Standalone boot prompt

The Python runner at `network/invoke_mia.py` assembles:
1. `agents/mia/persona.md`
2. `agents/mia/state.json`
3. `agents/mia/history.json` (last 10 entries)
4. `state/system_mode.json` and `state/user_state.json`
5. Relevant entries from `memory/emotional_memory.json`
6. The user's message
