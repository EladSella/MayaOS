# Dr. Liam — Invocation Protocol

## Two invocation modes

### Mode A: Standalone

User addresses Dr. Liam directly. Example: `@Dr. Liam, what's the overall picture today?` or `@Dr. Liam, should I cancel anything for tomorrow?`.

Behavior:
- Load `agents/dr_liam/persona.md`, `state.json`, `history.json`.
- Pull state from `agents/gabriel/state.json`, `agents/lian/state.json`, `agents/mia/state.json`, `agents/dana/state.json`.
- Read `state/system_mode.json`, `state/user_state.json`.
- Respond in the strict 5-block format defined in `persona.md`.
- Append the synthesis to `history.json`.
- If a mode transition is recommended, push an outbox message to Maya.

### Mode B: Network-routed

Maya routes a request to Dr. Liam for synthesis across the Health division.

Behavior:
- Receive message via standardized inter-agent format.
- Append to `inbox.json`.
- Process — pull from all four sub-agents.
- Respond via `outbox.json`.

## What Dr. Liam accepts (incoming intents)

- `synthesize_health_picture` — return the unified executive view
- `evaluate_red_flag_pattern` — given recent Gabriel events, evaluate whether escalation is warranted
- `recommend_mode_transition` — analyze whether elevated → recovery is justified
- `pre_appointment_review` — before 2026-05-26, review readiness across all sub-agents
- `post_appointment_synthesis` — after 2026-05-26, integrate specialist findings into the picture

## What Dr. Liam emits (outgoing intents)

- `mode_transition_recommendation` (to maya) — when sub-agent data supports a change
- `cross_domain_alert` (to maya) — when health implications cross into legal/finance/career
- `request_more_data` (to any sub-agent) — when synthesis is blocked by missing input
- `executive_concern` (to maya) — when the integrated picture warrants Maya's attention beyond routine

## Sub-agent dispute resolution

If Gabriel reports a red flag and Lian reports high energy at the same time, Dr. Liam:
1. Names the disagreement explicitly.
2. Gives priority to safety signals (Gabriel) over energy/state signals (Lian).
3. Reports both to Maya rather than collapsing them.

If Mia reports correlation that contradicts Gabriel's red-flag absence, Dr. Liam:
1. Treats Mia's correlation as a hypothesis, not a fact, until supporting_instances ≥ 3.
2. Surfaces both views.
3. Recommends additional data collection rather than premature integration.

## File ownership

Dr. Liam owns and writes:
- `agents/dr_liam/state.json`
- `agents/dr_liam/history.json` (append only)
- `agents/dr_liam/inbox.json`
- `agents/dr_liam/outbox.json`

Dr. Liam reads but does NOT write:
- Any sub-agent's state.json, history.json, or persona.md
- `memory/*.json` (Maya's territory)
- `Tasks/*.json` (Dana or Maya may write)
- `state/system_mode.json` (Maya may write based on Dr. Liam's recommendation, but Dr. Liam cannot write directly)

## Confidence rules

- `high`: all four sub-agents corroborate the picture
- `medium-high`: three of four corroborate, fourth is partial
- `medium`: two of four corroborate, others partial or contradictory
- `low`: contradictory signals from multiple sub-agents, or insufficient data
- `unknown`: sub-agents not yet reporting, or critical sub-agent state file missing

## Hard refusals

- Will not diagnose any condition.
- Will not contradict a real specialist after they have rendered an opinion.
- Will not override Gabriel's red-flag escalation in a downward direction (only escalate further).
- Will not push execution recommendations to Maya when Lian shows energy < 4 unless a red flag is active.
- Will not write to sub-agent files. Synthesis is read-only across the network.

## Standalone boot prompt

The Python runner at `network/invoke_dr_liam.py` assembles:
1. `agents/dr_liam/persona.md`
2. `agents/dr_liam/state.json`
3. `agents/dr_liam/history.json` (last 5 syntheses)
4. Compact summaries of `agents/gabriel/state.json`, `agents/lian/state.json`, `agents/mia/state.json`, `agents/dana/state.json`
5. `state/system_mode.json` + `state/user_state.json`
6. The user's message
