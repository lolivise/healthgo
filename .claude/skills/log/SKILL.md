---
name: log
description: Record health data Garmin never sees into the healthgo repo — an InBody scan (photo of the printout or numbers), an eating-out meal, blood-test results, a manual weight, or a free note. Opus reads the input, a Sonnet health-ops agent records, compares and commits. Trigger on /log, "here's my InBody", "I ate out", "my blood test results", or when Darren sends an InBody/bloodwork photo.
---

# /log

The split follows `CLAUDE.md` → Model split:
- **Opus (main thread):** reads what Darren sent and turns it into exact values.
- **`health-ops` (Sonnet):** records them, compares them with history, and commits.
- **Opus:** gives the one-line confirmation in 繁中.

## 1. Extract: Opus

The photo or text is already in your context, so read it here. Don't make an agent re-read it.

| Kind | Values to extract |
|---|---|
| InBody | `date`, `weight_kg`, `body_fat_pct`, `skeletal_muscle_kg`, `fat_mass_kg`, `visceral_fat_level`, plus **everything else** on the printout (body water, protein, minerals, BMR, InBody score, segmental values) under `other` |
| Eating out | `date`, `meal` (lunch/dinner/…), `description`, `est_kcal`: your estimate for a realistic restaurant portion |
| Bloodwork | `date`, `results` {name: value with units as printed}, `lab`, `flags` (anything outside the reference range) |
| Weight | `date`, `kg`, `source: "manual"` |
| Note | `date`, `text` (injury, illness, sleep disruption, …) |

- Dates default to today in Perth time.
- **Telegram inbox:** `/log` with no input (or "check my inbox") → run `uv run healthgo inbox && uv run healthgo inbox --list`,
  read each pending `data/inbox/<stem>.json` and its photo, and extract from those. The entry's date is the filename
  date unless the text says otherwise (e.g. "/eat yesterday dinner…"). Tell `health-ops` to run
  `uv run healthgo inbox --done <id> …` after recording.
- If a number is unreadable or the date is ambiguous, ask Darren. Don't guess.

## 2. Record: `health-ops` agent (Sonnet)

Brief it with the kind and the exact JSON. It runs `uv run healthgo add <kind> '<json>'`, then:
- **InBody:** compares with the previous scan (`SELECT * FROM inbody ORDER BY date`) and reports deltas.
- **Bloodwork:** lists out-of-range values, liver panel first (ALT, AST, GGT, bilirubin, hepatitis B markers).

It then commits and pushes (`log: <kind> <date>`).

## 3. Confirm: Opus

One or two lines in 繁中:
- **InBody:** flag a skeletal-muscle drop of 0.5 kg or more against the previous scan.
- **Eating out:** say the kcal is an estimate, and don't moralise; eating out is part of the plan.
- **Bloodwork:** out-of-range values → "worth raising with your doctor", never a diagnosis. He has Hep B,
  so mention liver values explicitly.
- If the entry changes the picture (e.g. a big muscle drop), say so and suggest running `/review`.
