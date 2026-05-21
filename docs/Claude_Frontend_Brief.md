# Claude Frontend Work Brief — MayaOS Health Dashboard

**For:** Claude
**From:** Gravity (MayaOS Orchestrator)
**Date:** 2026-05-20

## 1. Mission
Your task is to build the first UI screen for MayaOS — the **Mobile Health Dashboard**. 
Currently, MayaOS operates strictly via JSON state files, Python runners, and Markdown logs. The user needs a visual representation of their current health status and upcoming tasks to reduce cognitive load.

## 2. Technical Constraints
- **NO NODE.JS:** The local environment does not have Node/NPM installed. 
- **Tech Stack:** You must build this using strictly **Vanilla HTML, CSS, and JavaScript**. No React, no Vite, no Tailwind.
- **Execution:** Provide the code so the user can save it as an `index.html` (and optionally linked `.css`/`.js` files) and open it directly in the browser.

## 3. Design Aesthetics (CRITICAL)
- **Vibe:** Sleek, modern, premium, "Cognitive Operating System".
- **Theme:** Dark mode with subtle glassmorphism (translucent, blurred panels).
- **Colors:** Deep background (e.g., `#0f172a`), with neon blue and purple gradient accents.
- **Typography:** Use a modern Google Font (e.g., Inter, Outfit, or Roboto).
- **Responsiveness:** It must be a mobile-first design (max-width wrapper centered on desktop).

## 4. Required UI Sections

### A. Header / Executive Status (Dr. Liam)
- Show the division name: "MayaOS | Health Division"
- Show current active mode: `post_hospitalization_recovery`
- Status Indicator: "System Stable - No Active Red Flags"

### B. Medical Timeline (Gabriel & Mia)
Render a chronological timeline of recent events. Mock this data visually in the HTML:
- **May 14:** Acute GI Episode (Vomiting, Weakness), Left Arm Tingling begins.
- **May 15-16:** Hospitalization (Meir Medical Center) — Diagnosed with Acute Gastroenteritis.
- **May 19:** Lawyer Payment Pressure (Stress 5/10).
- **May 20:** Hand Discoloration Episode (Fear 8/10).

### C. Upcoming Appointments (Dana)
Show countdowns or cards for the Tuesday, May 26 appointments:
- **18:30 - Rheumatologist:** (Requires: discharge summary, blood tests, referrals).
- **20:00 - Psychiatrist:** (Requires: stress timeline, 2 distinct receipts).

## 5. Instructions for Claude
1. Generate the fully functional HTML/CSS/JS code.
2. Ensure the CSS includes modern animations (e.g., a slow pulse on the status indicator, smooth hover states on the timeline cards).
3. Do not invent new medical data; use the mocked data provided above.
4. Provide clear instructions to the user on how to save and open the file.
