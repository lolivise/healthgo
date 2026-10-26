# Research knowledge base

Two layers per topic:

- **Evidence summaries** in `.claude/memory/evidence-*.md`: the distilled, applied-to-Darren findings that reviews cite.
  Each one carries `sector:` in its frontmatter.
- **Full reports** (繁中) in `research/<sector>/`, with the raw research notes behind them in
  `research/<sector>/notes/<report name>/`.

A report that spans sectors lives in its main sector and is cross-listed in the others below. New research is
filed into its sector folder, never a flat `reports/` folder.

## Access

- **PubMed / PMC (NCBI E-utilities):** full open-access text and abstracts. The NCBI API key (10 req/s instead
  of 3) is in 1Password at `HealthGo/secrets` → `NCBI/API_key`. Read it with `healthgo.vault.read("NCBI/API_key")`
  (the service-account token; a plain `op read` with the personal login can't see the vault). Never print it.
- **Paywalled papers** (Springer, Elsevier, Wiley) and books: abstract only. Darren supplies the PDFs that matter.

## Quarterly review: `/knowledge-review`

- **Pull (no tokens):** `uv run healthgo pubmed --sector <s>` writes everything PubMed added since the sector's
  `last_reviewed` (meta-analyses, systematic reviews, RCTs) to `research/<s>/reviews/<quarter>-pulled.md`, git-ignored,
  title index first. Searches and dates: `config/research.json`.
- **Screen (Sonnet `health-research`, one per sector):** reads the index, opens only the abstracts that matter,
  returns a ≤50-line delta.
- **Decide (Opus):** rewrites evidence rows in place, logs each change in one line in `research/<s>/CHANGELOG.md`.

**Lean rule:** an evidence file is the current best answer, not a history. Contradicted rows are replaced, not kept;
each file stays ≤ ~50 lines; raw pulls are deleted; reports stay frozen snapshots with a one-line banner when
overturned. Full rules in `.claude/skills/knowledge-review/SKILL.md`.

## Sectors

Sectors 1–4 are reviewed every quarter (`last_reviewed` per sector in `config/research.json`). Sectors 5–6 are
practical and only refreshed on demand (a purchase, a new problem).

### 1. Fat loss & energy balance (`fat-loss`) · quarterly

Search area: deficit size, rate %/wk, energy availability (EA) / RED-S, adaptive thermogenesis, diet breaks,
reverse diet vs straight to maintenance, protein and fat floors in a deficit.

| Evidence | Researched |
|---|---|
| `evidence-cutting` | 2026-10-10 |
| `evidence-rapid-loss-harms` | 2026-10-25 |
| `evidence-max-fat-loss-rate` | 2026-10-25 |
| `evidence-metabolic-adaptation` | 2026-10-12 |
| `evidence-maintenance-transition` | 2026-10-10 |
| `evidence-muscle-turnover` | 2026-10-16 |
| `evidence-fasted-exercise` | 2026-10-16 |

Reports: cross-listed `medical/慢性發炎 減重過快 臉部老化.md` (the too-fast-loss section; notes
`rapid_weight_loss_harms.md`).

### 2. Training & muscle growth (`training`) · quarterly

Search area: volume, proximity to failure, load and rep range, long-length training, concurrent training,
recomposition, lean bulk, detraining.

| Evidence | Researched |
|---|---|
| `evidence-hypertrophy-training` | 2026-10-10 |
| `evidence-load-reps-stretch` | 2026-10-21 |
| `evidence-body-fat-and-muscle-growth` | 2026-10-20 |

Reports: none yet.

### 3. Medical: Hep B, inflammation, immunity (`medical`) · quarterly

Search area: HBV + metabolic risk, entecavir, ALT, hs-CRP, sleep and immunity, alcohol / ALDH2, Taiwan
population norms.

| Evidence | Researched |
|---|---|
| `evidence-inflammation-immunity-hepb` | 2026-10-25 |
| `evidence-asian-hepb` | 2026-10-10 |

Reports: `medical/慢性發炎 減重過快 臉部老化.md` (notes: `inflammation_drivers_markers`,
`inflammation_prevention`, `immunity_viral_hepb`).

### 4. Aging & longevity (`aging`) · quarterly

Search area: arterial stiffness, resistance + aerobic training and mortality, skin / collagen / UV, sleep
hygiene.

| Evidence | Researched |
|---|---|
| `evidence-exercise-and-aging` | 2026-10-25 |
| `evidence-facial-aging` | 2026-10-25 |
| `evidence-ikeya-anti-aging` | 2026-10-25 |

Reports: `aging/運動會讓人老得快嗎 池谷敏郎 血管.md`, `aging/池谷敏郎 抗老建議 逐條查證.md`; cross-listed
`medical/慢性發炎 減重過快 臉部老化.md` (notes `facial_aging_collagen.md`).

### 5. Measurement & tools (`measurement`) · on demand

Reports: `measurement/Home body fat scales comparison.md`. Applied in memory `data-sources`.

### 6. Food & kitchen (`food`) · on demand

Reports: `food/Chicken breast texture fix.md`. Applied in memory `chicken-marinades`.

## Known gaps for the first quarterly review

- Over the ~50-line budget already: `evidence-inflammation-immunity-hepb` (~77), `evidence-rapid-loss-harms` (~59).
  Condense them at the first review of their sectors.
- `evidence-cutting` and `evidence-hypertrophy-training` still have many **[M]** rows (model memory, never checked
  online): Garthe, Morton, Helms, Nedeltcheva, Bickel, Spiering, Refalo, Lopez, Schoenfeld, Bosquet, Iraki,
  Barakat. Check them first.
- Sector 2 has no full report behind its evidence.
- Timing: the first review falls around 2027-01, but he's in Taiwan 2027-01-23 → 02-25. Run it before the
  trip or after it.
