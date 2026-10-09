---
name: feel-checkin
description: The Telegram /feel symptom check-in (agreed 2026-10-09) — its questions, what was dropped and why, and the ~2026-11-09 one-month review of it
metadata:
  type: project
---

**/feel** is a tap-driven check-in in the Telegram bot. Darren uses it **when something feels wrong**, not daily.
It was drafted from the Hooper index, the IOC 2023 REDs consensus, the Meeusen 2013 overtraining consensus, and
healthdirect / the Hep B Foundation (HBV symptoms). He approved it on 2026-10-09.

The questions are:
- **Core**
  - Q1, what feels off (multi-select): hungry, dizzy, headache, fatigue, poor sleep, low mood or irritable,
    muscle or joint pain, GI, sick, other, 🚨 urgent.
  - Q2, severity 1–5.
  - Q3, since when.
  - Q4, likely cause (multi-select).
  - Q5, optional free text.
- **Branches:**
  - B1, dizzy: when it happens, and palpitations, cold sweat or shaking.
  - B2, hunger compared with usual.
  - B3, fatigue: training performance this week.
  - B4, pain: where, and whether it limits training.
  - B6, the **Hep B symptom check**, shown only on fatigue, GI or sick.
  - 🚨 ends the check-in with "see a doctor / call 000".
- **Not tracked: libido.** He dropped it, saying "I am low on these kind of thing anyway". Don't re-add it, and
  don't use libido as a low-energy-availability (REDs) signal for him.
- Garmin already covers sleep hours, stress and HRV, so the check-in doesn't ask about them.

**How to apply:**
- In `/review`, `feel` entries are subjective signals. Read them next to Garmin recovery.
- Any B6 symptom, or B1 with palpitations, cold sweat or shaking, means a doctor referral. Say so plainly
  ([[safety-limits]], [[health-conditions]]).
- At the first review on or after **2026-11-09**, ask him once which questions to add or remove.

The first logged episode was on 2026-10-09: hunger, dizziness and a headache in the afternoon, before /feel existed,
logged as notes. Related: [[daily-diet-baseline]], [[model-split]].
