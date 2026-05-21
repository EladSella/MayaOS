# Anti-Gravity Boot Instruction

Copy-paste the block below into Anti-Gravity as your first message. It is self-contained — AG does not need any prior context.

---

## Boot prompt (copy from here)

```
You are working on the MayaOS repository at the path the user opened.

Your work assignment is in `docs/AntiGravity_Work_Brief.md`. Read it first, in full.

Then read, in order, the four files it lists in §2:
1. AGENTS.md (at repo root)
2. agents_manifest.json (at repo root)
3. configs/core_rules.md
4. docs/AntiGravity_Build_Instructions_Health_Agent.md

After reading, run the kickoff checklist in the work brief §8:
1. Run `python network/invoke_dana.py --gaps` and capture the output.
2. Run `python network/invoke_gabriel.py --status` to verify the runner.
3. Run `python network/invoke_lian.py --status` to verify the runner.
4. Decide which Priority 1 task to start with. The recommendation is P1.2 (rheumatology briefing assembly) because it has the most fillable content from existing files.
5. Create `docs/AG_Worklog.md` and write your first entry per the format in §6.

Operate strictly within the V2-partial activation scope. Do not build new divisions, modify governance, or activate planned-but-frozen agents. Follow priority order: complete or block on P1 before P2, P2 before P3, and never start P4 without explicit user approval from Elad.

Report every action to `docs/AG_Worklog.md` (append-only). When a task is blocked, when something is unclear, or when you would need to violate a hard refusal, stop and write `## QUESTION FOR ELAD` in the worklog and wait.

Do not invent medical content. Only assemble from existing files. Mark every unfilled slot with `[NEEDS USER INPUT]`.

Begin.
```

## End of boot prompt

After AG runs, check `docs/AG_Worklog.md` to see what it did. If you see `## QUESTION FOR ELAD` entries, those are blockers waiting for your input.
