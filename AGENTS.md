# AGENTS.md — MayaOS Agent Network

This file is the discovery entry point for any agentic tool (Anti-Gravity, Claude, Cursor, etc.) opening this repository. Read this before touching anything.

## What this repo is

MayaOS is a personal "Cognitive Operating System" for Elad Sela — a hierarchical AI agent network with a Supreme CEO agent (Maya) coordinating multiple executive divisions, each with sub-agents.

## Current activation state

| Layer | Status |
|-------|--------|
| V1 (base) | FROZEN. Three executive personas: Maya, Amir, Daniel. Operate via prompt routing over JSON state files. |
| V2-partial (active) | Health division (Dr. Liam) + one Admin sub-agent (Chen). Activated 2026-05-20. |
| V2-full | NOT ACTIVE. Other divisions (Career, Relationship, Ayala, Property, Events, full Admin) are planned but frozen. |

Read `configs/core_rules.md` for the freeze directive and the V2 partial activation directive in full. Do not violate them.

## Built V2 agents (5 — all in folder-based structure)

Canonical location: `agents/<name>/` with six files each. Each agent has a Python runner in `network/invoke_<name>.py`.

| Agent | Role | Data model | Runner commands |
|-------|------|------------|-----------------|
| **Lian** | Energy Monitoring | continuous readings (energy, stress, focus 1-10) | `--status`, `--log`, `<message>` |
| **Gabriel** | Emergency Health / Triage | discrete events with red-flag pre-screen | `--status`, `--log`, `--check` (English+Hebrew), `<message>` |
| **Dana** | Medical Appointments | appointments + document checklist | `--status`, `--gaps`, `--got`, `--ref`, `<message>` |
| **Mia** | Stress Regulation | stress observations + correlations | `--status`, `--correlations`, `--log`, `<message>` |
| **Leo** | Healthy Lifestyle | fitness, nutrition, meditation tracking | `--status`, `--log`, `<message>` |

For programmatic discovery, see `agents_manifest.json` at the repo root.

## Agent folder structure (canonical)

Each agent's folder contains exactly these six files:

```
agents/<name>/
├── persona.md       # Who they are, voice, values, response format
├── state.json       # Current internal state (overwritten when changed)
├── history.json     # Append-only event log
├── inbox.json       # Incoming inter-agent messages
├── outbox.json      # Outgoing inter-agent messages
└── protocol.md      # Invocation modes, accepted/emitted intents, ownership rules
```

## Inter-agent message schema

All agents communicate via `network/message_schema.json`. Required fields: `msg_id`, `timestamp`, `from`, `to`, `type` (request/response/broadcast/alert), `payload` (with `intent`, `data`, optional `context_refs`), `confidence_level`, `requires_response`.

## How to invoke an agent

### Standalone (recommended for direct interaction)

```bash
python network/invoke_lian.py "How am I doing today?"
python network/invoke_gabriel.py --check "ידיים מכחילות עם כאב חזק"
python network/invoke_dana.py --status
python network/invoke_mia.py --log "stressor=lawyer intensity=7 somatic=chest_tightness"
python network/invoke_leo.py "Give me today's meditation link"
```

Each runner has two output behaviors:
- Quick commands (`--status`, `--log`, `--check`, `--gaps`, `--got`, `--correlations`) print JSON to stdout and may update state/history files.
- A message argument (no flag) prints a **boot prompt** to stdout. That prompt is meant to be piped into any LLM, which will then respond AS the agent in their strict response format.

The runners do NOT call any LLM. They build the prompt; the LLM environment runs it.

### Network mode (Maya routes)

Maya (CEO) receives a user message and decides which sub-agent to consult. Messages are written to that agent's `inbox.json` in the standard schema. The agent processes, responds via `outbox.json`. Maya synthesizes.

## What you (AG, Claude, etc.) may modify

Safe to touch:
- `agents/<name>/state.json` — only when invoking the agent has caused a state change.
- `agents/<name>/history.json` — append only, never overwrite or delete entries.
- `agents/<name>/inbox.json` and `outbox.json` — process and add as needed.
- `Tasks/*.json` — per the task lifecycle workflow.
- `memory/*.json` — append only.

Do NOT touch without explicit user directive:
- `configs/core_rules.md` — governance. Lock.
- `configs/agents_registry.json` — registry. Only when adding/activating an agent under explicit user directive.
- Any agent's `persona.md` or `protocol.md` — locked unless user explicitly wants persona evolution.
- Agents that don't yet exist as folders — do not create new divisions or sub-agents without user directive.

## What is forbidden in V2-partial

- Building Career, Relationship, Ayala, Property, Events, or full Admin divisions.
- Building autonomous loops / cron jobs.
- Building external API integrations (WhatsApp, Gmail, Calendar, Bank, Voice) EXCEPT for Icon Fitness integration (granted by CEO override on 2026-05-21).
- Building vector DB memory.
- Building meta-agents (Shadow, Focus, Life Balance, Crisis Prevention).
- Letting any agent claim medical, legal, or financial diagnostic authority.

If you (the tool) think one of these is necessary, escalate to user. Do not act.

## How to extend (build a new agent)

If the user explicitly directs you to build a new agent:

1. Create folder `agents/<name>/` with all six standard files.
2. Follow the existing personas (Lian, Gabriel, Dana, Mia) as templates.
3. Create a Python runner at `network/invoke_<name>.py` following the existing pattern.
4. Update `configs/agents_registry.json` `agent_directories` section.
5. Update `agents_manifest.json`.
6. Update this `AGENTS.md`.
7. Validate: all JSONs parse, all runner --status calls return JSON, registry references resolve.

## Known technical notes

- Some Edit-tool environments truncate Python files containing certain string patterns (e.g., `.replace(" ", "_")` chains). If you hit this, use shell heredoc to write the file instead.
- The `Tasks/` directory has a capital T. Hebrew text is supported throughout — UTF-8 with `ensure_ascii=False` in JSON dumps.
- One legacy file `logs/system_validation_2026_05_19.json` contains plain text despite its `.json` extension. Pre-existing; not part of the V2 build.

## Reference docs

- `docs/Claude_Orientation_Brief.md` — original V1 orientation.
- `docs/AntiGravity_Build_Instructions_Health_Agent.md` — full build spec for handoff to AG. Reflects current built state.
- `configs/core_rules.md` — governance.
- `prompts/dr_liam_master_prompt.txt` — Health division executive master prompt.
- `prompts/maya_master_prompt.txt` — Maya CEO master prompt (note: this file still describes the V2 full architecture; treat it as the long-term blueprint, not the current operational scope).
