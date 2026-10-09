---
name: log
description: Record health data Garmin never sees into the healthgo repo — an InBody scan (photo of the printout or numbers), an eating-out meal, blood-test results, a manual weight, or a free note. A Sonnet health-ops agent reads any photo, records, compares and commits; Opus only handles text input and the confirmation. Trigger on /log, "here's my InBody", "I ate out", "my blood test results", or when Darren sends an InBody/bloodwork photo.
---

# /log

The split follows `CLAUDE.md` → Model split:
- **Images are always read by `health-ops` (Sonnet), never by Opus.** Darren, 2026-10-09: "when doing any images
  parsing, use sonnet agent. do not use opus. it will be overkilled".
- **Opus (main thread):** turns *text* input into exact values.
- **`health-ops` (Sonnet):** extracts values from photos, records everything, compares with history, and commits.
- **Opus:** gives the one-line confirmation in 繁中.

## 1. Extract: Opus for text, `health-ops` for images

- **Text** (e.g. "/eat Korean BBQ with friends", "InBody 90.2 kg 24.8 %"): Opus extracts the values below.
- **Images** (an InBody printout, a blood report, a meal photo): **don't read them in the main thread.** Pass the
  file path to `health-ops` in step 2 with the field list below, and it reads the image and extracts the values.
  Telegram inbox photos are files under `data/inbox/`. A photo pasted straight into this chat has no file path, so
  ask Darren to send it through the bot's `/inbody` / `/blood` / `/eat` menu instead.

| Kind | Values to extract |
|---|---|
| InBody | `date`, `weight_kg`, `body_fat_pct`, `skeletal_muscle_kg`, `fat_mass_kg`, `visceral_fat_level`, plus **everything else** on the printout (body water, protein, minerals, BMR, InBody score, segmental values) under `other` |
| Eating out | `date`, `meal` (lunch/dinner/…), `description`, `est_kcal`: your estimate for a realistic restaurant portion |
| Bloodwork | `date`, `results` {name: value with units as printed}, `lab`, `flags` (anything outside the reference range) |
| Weight | `date`, `kg`, `source: "manual"` |
| Note | `date`, `text` (injury, illness, sleep disruption, …) |

- Dates default to today in Perth time.
- **Telegram inbox:** `/log` with no input (or "check my inbox") → run `uv run healthgo inbox && uv run healthgo inbox --list`,
  read each pending `data/inbox/<stem>.json` (text only); entries with a photo go to `health-ops` by path. The entry's date is the filename
  date unless the text says otherwise (e.g. "/eat yesterday dinner…"). Tell `health-ops` to run
  `uv run healthgo inbox --done <id> …` after recording.
- If a number is unreadable or the date is ambiguous, ask Darren. Don't guess.

## 2. Record: `health-ops` agent (Sonnet)

Brief it with the kind and either the exact JSON (text input) or the image path plus the step 1 field list, and
for a meal photo, tell it to estimate `est_kcal` for a realistic restaurant portion. It must return the values it
extracted (as JSON) so Opus can check them, and it must mark an unreadable number as `null` with a note instead of guessing (Opus then asks Darren). It runs `uv run healthgo add <kind> '<json>'`, then:
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
