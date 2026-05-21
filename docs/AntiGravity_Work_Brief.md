# Anti-Gravity Work Brief — MayaOS Health Division

**For:** Anti-Gravity (or any parallel agentic tool)
**Owner:** Elad Sela
**Issued:** 2026-05-20
**Time horizon:** 6 days until critical milestone (appointments 2026-05-26 evening)

This is a focused work order. Read this first, then read the four required files in §2, then start at Priority 1.

---

## 1. Mission

Operate and refine the existing MayaOS Health agent network to support an active medical situation. Do NOT build new divisions or invent new structures. Work within the V2-partial activation scope already in place.

The four active agents (Lian, Gabriel, Dana, Mia) already exist with full personas, state, history, protocols, and Python runners. Your job is to operate them well, fill in gaps in their state, and produce the deliverables Elad needs for Tuesday's two specialist appointments.

---

## 2. Required reading before starting (4 files, in order)

1. `AGENTS.md` — entry-point discovery doc.
2. `agents_manifest.json` — agent inventory.
3. `configs/core_rules.md` — governance and V2-partial directive. Hard rules.
4. `docs/AntiGravity_Build_Instructions_Health_Agent.md` — full operations guide.

Optional but recommended: each active agent's `protocol.md` so you know what intents they accept and emit.

---

## 3. Hard constraints (read twice)

You may NOT, without explicit user directive from Elad:

- Create new divisions (Career, Relationship, Ayala, Property, Events, full Admin).
- Create meta-agents (Shadow, Focus, Life Balance, Crisis Prevention).
- Add autonomous loops, cron jobs, or background tasks.
- Add external API integrations (WhatsApp, Gmail, Calendar, Bank, Voice).
- Add vector DB memory or any embedding store.
- Modify `configs/core_rules.md` (governance is locked).
- Modify any agent's `persona.md` or `protocol.md` (locked).
- Have any agent claim medical, legal, or financial diagnostic authority.

If you think one of the above is necessary, stop and report to Elad. Do not act.

---

## 4. Task queue (priority order)

### PRIORITY 1 — Tuesday 2026-05-26 appointment readiness (6 days)

These are the most time-sensitive tasks. Two appointments: rheumatologist 18:30, psychiatrist 20:00. Dana has 11 active document gaps.

**P1.1 — Track and reduce Dana's gaps**
- Run `python network/invoke_dana.py --gaps` to see current gap list.
- For each gap with owner "Elad (manual)", remind Elad explicitly with the document name and the days remaining.
- When a document arrives, call `python network/invoke_dana.py --got <doc_id> --ref <path or note>`.
- **Done when:** all 9 required documents are obtained OR explicitly flagged as unrecoverable.

**P1.2 — Assemble the rheumatology briefing document**
- Target file: `Tasks/briefings/rheumatology_2026_05_26.md` (create folder if missing).
- Structure per Dana's protocol.md §"Briefing assembly":
  1. Chief complaint (one sentence — from user)
  2. Timeline (from `agents/gabriel/history.json` events, chronological)
  3. Evidence (photo references, blood test references, discharge summary reference)
  4. Hypotheses already considered (from `agents/gabriel/state.json` `monitored_hypotheses`)
  5. Specific questions for the rheumatologist (drafted, user finalizes)
  6. Medications and supplements (slot for user to fill)
  7. Relevant prior care (weekend hospitalization context)
- **Critical**: do NOT invent medical content. Only assemble from existing files.
- **Done when:** all 7 sections drafted, with explicit `[NEEDS USER INPUT]` markers wherever data is missing.

**P1.3 — Assemble the psychiatric briefing document**
- Target file: `Tasks/briefings/psychiatry_2026_05_26.md`.
- Structure per Mia's protocol.md §"Briefing draft sections":
  1. Background psychological state (from `memory/emotional_memory.json`)
  2. Stress timeline (chronological list from `agents/mia/history.json`)
  3. Somatic-anxiety correlations observed (only those with confidence ≥ medium — currently NONE meet this bar, so this section will note "insufficient data, single observation only")
  4. Sleep / eating / cognitive changes (slot for user)
  5. Current medications and recent changes (slot for user)
  6. Specific questions for the psychiatrist (drafted)
- **Done when:** all 6 sections drafted with `[NEEDS USER INPUT]` markers.

**P1.4 — Build the stress timeline document (subtask of P1.3)**
- Target file: `Tasks/briefings/stress_timeline_2026_05_26.md`.
- Pull from `agents/mia/history.json` + `memory/emotional_memory.json`.
- Chronological, factual, no interpretation.

**P1.5 — Verify insurance reimbursement coverage (Chen task)**
- Chen does not call insurance. Chen produces a checklist for Elad to file.
- Target file: `Tasks/briefings/insurance_checklist_2026_05_26.md`.
- Contents: per-appointment, list of documents needed for reimbursement claim, deadline, where to submit.

### PRIORITY 2 — Daily operations during the lead-up

**P2.1 — Daily Lian reading**
- Each day until 2026-05-26: append a reading via `python network/invoke_lian.py --log "energy=N stress=N focus=N context=daily_checkin_YYYY_MM_DD"`.
- If energy drops by >2 in a day, push an outbox message from Lian to Dr. Liam with intent `energy_delta_alert`.

**P2.2 — Symptom episode logging**
- Whenever a hand discoloration or other episode occurs, run `python network/invoke_gabriel.py --check "<symptom description in English or Hebrew>"` first.
- If the assessment is `GO_TO_ER`, the script's job is done — Elad must act.
- Otherwise, log via `python network/invoke_gabriel.py --log "symptom=... side=... duration=... outcome=..."`.

**P2.3 — Pattern check (Mia)**
- After 3+ symptom episodes are logged, run `python network/invoke_mia.py --correlations` and check if any correlation has reached `supporting_instances >= 3`.
- If yes, propose a memory entry update to Maya (do not write directly to `memory/emotional_memory.json` — that's Maya's territory).

### PRIORITY 3 — Polish (only after P1 is complete or blocked on user input)

**P3.1 — Per-agent README inside each folder**
- For each of `agents/lian/`, `agents/gabriel/`, `agents/dana/`, `agents/mia/`: add a short `README.md` (10–20 lines) summarizing the agent's purpose, the 4-block response format, and one example invocation.

**P3.2 — Extend `--check` style pre-screen to Mia**
- Mia could benefit from a simple keyword pre-screen for high-intensity stress descriptions (e.g., "panic", "התקף חרדה").
- Add `--check` to `network/invoke_mia.py` following Gabriel's pattern.
- Output should help triage whether to escalate to Dr. Liam or wait.

**P3.3 — Unified dispatcher (optional)**
- `network/invoke.py` that takes `<agent_name> [args]` and dispatches to the right runner.
- Useful for AG and other tools to have a single entry point.

### PRIORITY 4 — Reserved (requires explicit user directive)

**P4.1 — Build Eva (Sleep Agent) under Dr. Liam**
- Lian's state has flagged `Sleep quality is not currently tracked` as an open question.
- DO NOT build Eva unless Elad explicitly says "build Eva".
- If built: follow the same folder + runner template; update registry, manifest, AGENTS.md.

**P4.2 — Build Maya CEO router skeleton**
- Maya currently exists only as a persona file and master prompt. There is no folder structure, no runner, no inbox/outbox.
- A router skeleton would tie the four sub-agents together — when a user message arrives, Maya decides which sub-agent(s) to consult, collects their responses, synthesizes.
- DO NOT build this unless Elad explicitly says "build Maya router".

---

## 5. Acceptance criteria (how to know you're done)

| Task | Acceptance |
|------|-----------|
| Briefing document | All required sections present. `[NEEDS USER INPUT]` markers on any unfilled slot. No invented medical content. |
| --got call | Returns success, state.json shows `obtained: true` for the doc, alerts recalculated. |
| Daily reading | history.json shows the new entry. state.json `current_reading` matches the new values. |
| Symptom log | history.json appended. event_id is unique. state.json `last_episode_*` updated. |
| New file | JSON parses, Python syntax valid, registry/manifest/AGENTS.md updated where relevant. |

Run the validation one-liner from `docs/AntiGravity_Build_Instructions_Health_Agent.md` §7 after any significant change. All checks must pass except the pre-existing legacy file.

---

## 6. Reporting back

Write a worklog at `docs/AG_Worklog.md`. Append-only. Each entry:

```
## YYYY-MM-DD HH:MM
- Task: <task id from this brief, e.g. P1.1>
- Action: <what you did>
- Files touched: <list>
- Outcome: <success / blocked / partial>
- Blockers (if any): <what's blocking, who can resolve>
- Confidence: high / medium / low
```

If you create new files, list them in the worklog. If you modify existing files, note which.

---

## 7. Hard refusals (must not happen)

- Writing medical diagnoses into any briefing.
- Calling out to LLMs from within the Python runners (the runners build prompts; they do not call models).
- Activating any planned-but-frozen division.
- Modifying any persona.md or protocol.md.
- Pushing execution recommendations during energy dips < 4 (see Lian's persona).
- Logging Elad's full medical reasoning as facts when they're hypotheses.

---

## 8. Kickoff checklist (first 5 things to do)

1. Read all 4 files in §2.
2. Run `python network/invoke_dana.py --gaps` and copy the output into `docs/AG_Worklog.md` as your starting state.
3. Run `python network/invoke_gabriel.py --status` and `python network/invoke_lian.py --status` to confirm the runners work.
4. Decide which P1 task to start with (recommend P1.2 — rheumatology briefing, since it has the most fillable content from existing files).
5. Log your first worklog entry.

---

## 9. When in doubt

- Stop.
- Read the relevant `persona.md` and `protocol.md` for the agent in question.
- If still unclear, write a question to `docs/AG_Worklog.md` under a `## QUESTION FOR ELAD` heading and pause.
- Do not guess on medical content or system architecture.

End of work brief.
