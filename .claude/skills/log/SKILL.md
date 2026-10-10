---
name: log
description: Record health data Garmin never sees into the healthgo repo — an eating-out meal, blood-test results, a manual weight, or a free note. A Sonnet health-ops agent reads any photo, records, compares and commits; Opus only handles text input and the confirmation. Trigger on /log, "I ate out", "my blood test results", or when Darren sends a meal/bloodwork photo.
---

# /log

The split follows `CLAUDE.md` → Model split:
- **Images are always read by `health-ops` (Sonnet), never by Opus.** Darren, 2026-10-09: "when doing any images
  parsing, use sonnet agent. do not use opus. it will be overkilled".
- **Opus (main thread):** turns *text* input into exact values.
- **`health-ops` (Sonnet):** extracts values from photos, records everything, compares with history, and commits.
  **Meal photos only:** spawn `health-ops` with `model: "haiku"` (Darren, 2026-10-09). The kcal is an estimate anyway.
  Bloodwork photos stay on Sonnet.
- **No InBody anymore** (gym removed the machine, 2026-10-10): `healthgo add` no longer accepts `inbody`. Anything he sends that
  looks like an InBody result is recorded as a plain note.
- Voice notes arrive already transcribed (Workers AI Whisper in the Worker). Treat the transcript as text. If the text
  is empty (transcription failed) and an `.oga` file is present, ask Darren what he said. Don't guess.
- **Opus:** gives the one-line confirmation in 繁中.

## 1. Extract: Opus for text, `health-ops` for images

- **Text** (e.g. "/eat Korean BBQ with friends"): Opus extracts the values below.
- **Images** (a blood report, a meal photo): **don't read them in the main thread.** Pass the
  file path to `health-ops` in step 2 with the field list below, and it reads the image and extracts the values.
  Telegram inbox photos are files under `data/inbox/`. A photo pasted straight into this chat has no file path, so
  ask Darren to send it through the bot's `/blood` / `/eat` menu instead.

| Kind | Values to extract |
|---|---|
| Eating out | `date`, `meal` (lunch/dinner/…), `description`, `est_kcal`: your estimate for a realistic restaurant portion |
| Bloodwork | `date`, `results` {name: value with units as printed}, `lab`, `flags` (anything outside the reference range) |
| Weight | `date`, `kg`, `source: "manual"` |
| Note | `date`, `text` (injury, illness, sleep disruption, …) |

- Dates default to today in Perth time.
- **Telegram inbox:** `/log` with no input (or "check my inbox") → run `uv run healthgo inbox && uv run healthgo inbox --list`,
  read each pending `data/inbox/<stem>.json` (text only); entries with a photo go to `health-ops` by path. The entry's date is the filename
  date unless the text says otherwise (e.g. "/eat yesterday dinner…"). Tell `health-ops` to run
  `uv run healthgo inbox --done <id> …` after recording.
- **`feel` entries** (the `/feel` check-in, see memory `feel-checkin.md`): record as a `note` whose text is the entry's
  summary, prefixed `[feel]`; mark `partial` / `urgent` if set. Any Hep B symptom (B6) or dizziness with palpitations,
  cold sweat or shaking → say "see a doctor" in the confirmation.
- If a number is unreadable or the date is ambiguous, ask Darren. Don't guess.

## 2. Record: `health-ops` agent (Sonnet)

Brief it with the kind and either the exact JSON (text input) or the image path plus the step 1 field list, and
for a meal photo, tell it to estimate `est_kcal` for a realistic restaurant portion. It must return the values it
extracted (as JSON) so Opus can check them, and it must mark an unreadable number as `null` with a note instead of guessing (Opus then asks Darren). It runs `uv run healthgo add <kind> '<json>'`, then:
- **Bloodwork:** lists out-of-range values, liver panel first (ALT, AST, GGT, bilirubin, hepatitis B markers).

It then commits and pushes (`log: <kind> <date>`).

## 3. Confirm: Opus

One or two lines in 繁中:
- **Eating out:** say the kcal is an estimate, and don't moralise; eating out is part of the plan.
- **Bloodwork:** out-of-range values → "worth raising with your doctor", never a diagnosis. He has Hep B,
  so mention liver values explicitly.
- If the entry changes the picture (e.g. a big strength drop), say so and suggest running `/review`.
