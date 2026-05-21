# MayaOS — Anti-Gravity Operations and Extension Guide

**Status:** Updated 2026-05-20 to reflect the **built** state. This is no longer a "how to build from scratch" doc — the four Health agents and Chen are already in place. This doc is for Anti-Gravity (or any parallel agentic tool) to **operate, extend, and verify** the system.

**Owner:** Elad Sela
**Repo root:** `MayaOS/`

---

## 1. What's already built (do not rebuild)

| Component | Status | Files |
|-----------|--------|-------|
| Governance (V1 freeze + V2-partial directive) | Active | `configs/core_rules.md` |
| Agent registry | Active | `configs/agents_registry.json` |
| Inter-agent message schema | Active | `network/message_schema.json` |
| Dr. Liam (Health Executive) | Active, single-file persona + master prompt | `agents/dr_liam_agent.txt`, `prompts/dr_liam_master_prompt.txt` |
| Lian (Energy Monitoring) | Active, folder + runner | `agents/lian/*`, `network/invoke_lian.py` |
| Gabriel (Emergency Triage) | Active, folder + runner, EN+HE | `agents/gabriel/*`, `network/invoke_gabriel.py` |
| Dana (Medical Appointments) | Active, folder + runner | `agents/dana/*`, `network/invoke_dana.py` |
| Mia (Stress Regulation) | Active, folder + runner | `agents/mia/*`, `network/invoke_mia.py` |
| Chen (Bureaucracy, insurance scope only) | Active, single-file persona | `agents/chen_agent.txt` |
| Memory updates (hospitalization, photo, appointments) | Logged | `memory/health_memory.json`, `memory/emotional_memory.json` |
| Task list for 2026-05-26 appointments | 9 tasks | `Tasks/health_tasks.json` |
| Root discovery doc | Active | `AGENTS.md` |
| Manifest | Active | `agents_manifest.json` |

**DO NOT recreate any of these.** Read them, extend them, validate them — but do not re-author them from scratch.

---

## 2. How to operate an existing agent (the common pattern)

Each folder-based agent (Lian, Gabriel, Dana, Mia) has the same six-file structure and a Python runner with four canonical modes:

1. `--status` — prints JSON snapshot of the agent's current state.
2. `--log` (or `--got` for Dana) — appends an event/reading/observation and updates state.
3. Domain-specific commands (`--check` for Gabriel red flags, `--gaps` for Dana, `--correlations` for Mia).
4. A bare message argument — prints the **boot prompt** (persona + state + history + system context + the user message) which can be piped to any LLM. The LLM then responds AS the agent.

The runners never call an LLM themselves. They build the prompt; the LLM environment runs it. This makes them portable across Anti-Gravity, Claude, ChatGPT, Cursor, or local models.

Example:

```bash
# Get the boot prompt and pipe it (illustrative)
python network/invoke_lian.py "what's my energy state?" | your_llm_cli
python network/invoke_gabriel.py --check "ידיים מכחילות עם כאב חזק"  # → GO_TO_ER
python network/invoke_dana.py --gaps                                  # → 11 gaps with days_remaining
python network/invoke_mia.py --status
```

---

## 3. Reasoning discipline (non-negotiable for all Health agents)

Inherits from `core_rules.md`, tightened for medical context:

1. **Four-layer separation**: observed → reported → hypothesized → recommended. Never collapse.
2. **No diagnostic claims**. Agents are not doctors. Use "consistent with" not "is".
3. **Plural hypotheses**. Single-explanation framing is forbidden under uncertainty.
4. **Confidence levels mandatory** on every inferential statement: `high | medium | low | unknown`.
5. **Red flags must always surface** when hand or circulation symptoms are reported.
6. **Cognitive load caps**: max 3 hypotheses, max 5 action items per response.
7. **Anti-escalation**: do not amplify fear, do not dismiss concern.
8. **Defer to specialists** for actual decisions.

---

## 4. Network protocol (how agents talk to each other)

All inter-agent messages use the schema in `network/message_schema.json`. Required fields:

- `msg_id`: unique identifier
- `timestamp`: ISO 8601 with timezone
- `from`: agent_id
- `to`: agent_id or "broadcast"
- `type`: "request" | "response" | "broadcast" | "alert"
- `payload`: `{ intent, data, context_refs }`
- `confidence_level`: high | medium | low | unknown
- `requires_response`: bool

Each agent's `protocol.md` lists the specific `intent` values it accepts (incoming) and emits (outgoing). Use those — do not invent new intents without updating the protocol file.

Messages are persisted to:
- `agents/<name>/inbox.json` — incoming
- `agents/<name>/outbox.json` — outgoing

These are append-only during routing; consume by removing processed entries.

---

## 5. How to extend (build a NEW sub-agent or division)

If — and only if — the user explicitly directs you to add a new agent:

1. Confirm the V2 directive in `core_rules.md` permits the activation (or update the directive with user's consent).
2. Create `agents/<new_name>/` with the six standard files. Use the existing four as templates.
3. Match the response-block format style: `READING / OBSERVATION / NOTE / NEXT` for Lian; `EVENT LOG / RED FLAG CHECK / INTERPRETATION / NEXT ACTION` for Gabriel; choose a coherent 3-4 block format for the new agent.
4. Create `network/invoke_<new_name>.py` following the existing runner pattern. The runner must:
   - Read persona, state, history, system_mode, user_state
   - Print a boot prompt for bare message
   - Implement `--status`, `--log`, and any domain-specific commands
   - Not call any LLM
5. Update `configs/agents_registry.json` `agent_directories`.
6. Update `agents_manifest.json`.
7. Update `AGENTS.md` agent table.
8. Validate (see §7).

---

## 6. What is FROZEN (do not touch)

Do not create or activate any of these without explicit user directive AND a matching update to `core_rules.md`:

- Career, Relationship, Ayala, Property, Events, full Admin divisions
- Meta-agents (Shadow, Focus, Life Balance, Crisis Prevention)
- Autonomous loops / cron jobs / background tasks
- External API integrations (WhatsApp, Gmail, Calendar, Bank APIs, Voice)
- Vector DB memory or any persistent embedding store
- Model routing layer (the Claude Opus / GPT-5 / GPT-4o tiering described in `maya_master_prompt.txt`)

The master prompt at `prompts/maya_master_prompt.txt` describes the full V2 architecture. Treat it as long-term blueprint, NOT current operational scope.

---

## 7. Validation checklist (run after any change)

```python
# Pseudo-validation. The actual one-liner is below.
1. All JSON files parse (use json.load on every *.json under repo root).
2. All Python runners parse (use ast.parse).
3. All agent folders have 6 files: persona.md, state.json, history.json, inbox.json, outbox.json, protocol.md.
4. Every runner --status returns valid JSON.
5. Every registry reference resolves to an existing file.
6. Gabriel --check returns GO_TO_ER for inputs with red-flag keywords in either language.
7. Dana --gaps reports correct count (= count of unobtained docs × required_for length).
```

One-liner (run from repo root):

```bash
python3 -c "
import json, ast, subprocess
from pathlib import Path
errors = []
for p in Path('.').glob('**/*.json'):
    if 'logs/system_validation_2026_05_19' in str(p): continue  # known legacy non-JSON
    try: json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p}: {e}')
for p in Path('network').glob('invoke_*.py'):
    try: ast.parse(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p}: {e}')
for agent in ['lian','gabriel','dana','mia']:
    r = subprocess.run(['python3', f'network/invoke_{agent}.py', '--status'], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip(): errors.append(f'{agent} --status broken')
print('OK' if not errors else 'FAIL: ' + '\\n'.join(errors))
"
```

---

## 8. Known technical notes for AG

- **Edit-tool truncation gotcha**: Some agentic editing tools truncate Python files when they encounter specific patterns like `.replace(" ", "_").replace("/", "_")`. If you hit this, write the file via shell heredoc (`cat > file.py <<'EOF' ... EOF`) instead of an in-line edit. This was hit during the original build and resolved.
- **`Tasks/` has a capital T** — this is intentional, do not "fix" it.
- **One legacy file** `logs/system_validation_2026_05_19.json` contains plain text despite the `.json` extension. Pre-existing pre-V2 issue. Do not validate against it.
- **Hebrew everywhere** — UTF-8 with `ensure_ascii=False` is required when writing JSON. The runners already do this.
- **Legacy `*_agent.txt` files** — files like `agents/lian_agent.txt` now contain a DEPRECATED pointer to the folder structure. Do not load them as persona files. Use `agents/<name>/persona.md`.

---

## 9. Active medical context (for situational awareness)

The Health division was activated because of an ongoing situation:

- Weekend hospitalization 2026-05-16/17 (discharge summary NOT yet in system — top priority gap)
- Acute event Thursday 2026-05-14 (vomiting, tremors, sweating; cardiac event ruled out)
- Ongoing hand discoloration with night-time clustering
- Two specialist appointments scheduled Tuesday 2026-05-26: rheumatologist 18:30, psychiatrist 20:00
- 11 document gaps tracked by Dana, 9 task items in `Tasks/health_tasks.json`

If AG is asked to "help with the appointments" or "track symptoms", route through the existing agents. Do not create parallel structures.

---

## 10. Handoff notes

- Treat the existing files as canonical. If you find inconsistencies between this doc and the files, the files win — and report the diff to Elad.
- The agent network is intentionally synchronous and file-based in V2-partial. Asynchronous execution is reserved for V2-full and is not yet permitted.
- All four runners have been validated. If a runner stops returning output, check syntax first (the truncation gotcha is the most likely culprit).

End of operations guide.
