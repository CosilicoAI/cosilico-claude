---
name: Microplex Synthetic Data
description: Use this skill when working on microplex, synthetic microdata quality, the eCPS replacement, or interpreting synthesis/calibration benchmark metrics. Covers the spec-driven architecture, repo map, evaluation protocol, and weighting guards.
version: 2.0.0
---

# Microplex: spec-driven microdata synthesis

Microplex is PolicyEngine's pipeline for building calibrated survey microdata,
on track to replace the Enhanced CPS (eCPS) as the canonical US dataset.
Architecture: a **pure declarative country pack** (YAML/JSON) executed by a
**generic engine**, with imputation, calibration, and entity construction
factored into sibling packages.

## Repo map (github.com/PolicyEngine, local clones in ~/CosilicoAI/)

| Repo | Role |
|---|---|
| `microplex` | The engine: spec loader, spine builder, imputation runner, transforms, Arch targets, calibration, eval |
| `microplex-us` | US content pack — YAML/JSON **only** (`src/microplex_us/specs/us-2024.yaml` + manifests). Zero Python by contract (AGENTS.md) |
| `microimpute` | Canonical regime-aware donor imputation (QRF) |
| `microcalibrate` | Identity-preserving gradient-descent calibration |
| `microunit` | Tax-unit/SPM/program unit construction (extracted byte-identically from eCPS) |
| `microplex-evals` | Frozen benchmark science — paper claims cite `artifacts/`, never console output |
| `policyengine-us-data` | The incumbent eCPS being replaced |

Targets come from **Arch** consumer-fact records via
`microplex.targets.arch_provider` plus the pack's `manifests/arch_targets.json`.

⚠️ **Branch gotcha:** the engine's de facto trunk has been the integration
branch `claude/spec-driven-engine`; `main` lagged far behind. Always
`git fetch` and check both before reading or citing engine code. The US spec
also exists in two copies (`microplex/packs/us/` and `microplex-us`) — check
which is ahead before editing either.

## The pipeline (`microplex.run.run_spec`)

spec (YAML) → sources → base imputation → **support spine** (seeded 50/50:
`cps_keep` passthrough half + `synthetic_puf` half stripped to demographics) →
halves imputation (microimpute) → declarative transforms → optional
PolicyEngine runtime ops (variable materialization, takeup rerandomization) →
Arch targets → sparse calibration → export. Check `PENDING_STAGES` in
`microplex/src/microplex/run.py` for stages not yet wired.

**Correctness anchor** (`docs/spec-driven-rebuild.md` §4): the synthetic half
must NEVER keep or condition on CPS wages — it carries the PUF's income tail.

## Evaluation: what actually exists

- `microplex.eval` — generic synthesis benchmarks: PRDC
  (precision/recall/density/coverage, via the `prdc` package), aggregate
  error, and method comparisons (QRF / ZI-QRF / QDNN / MAF).
- **eCPS-replacement protocol**: matched-N, symmetric-refit, **holdout**
  comparison on the same target surface; unweighted MSRE + per-target holdout
  wins. Frozen baseline:
  `microplex-us` `manifests/frozen_production_ecps_2024_benchmark_manifest.json`.
  The 2,223-line comparison harness was deleted in microplex-us#261 — recover
  from `microplex-us@f3af332` until it lands in `microplex.eval`
  (microplex-us#231, microplex-evals#1).
- **Authenticity vs privacy** (conceptual guardrail): synthetic records
  *should* resemble **holdout** data (the model learned the distribution);
  they should *not* resemble **training** data more closely (memorization).
  Public CPS donors carry no privacy risk; administrative donors do.

## Critical guards

1. **Entity-convergence guard (microplex-us#113):** `microunit` IS eCPS's
   tax-unit engine, so adopting it makes MP's entities converge toward
   eCPS's. A loss drop after adoption is convergence, NOT improvement. Never
   report "MP beats eCPS" off shared construction code — isolate the effect
   with a matched-N, symmetric-refit, holdout before/after run.
2. **Aggregates:** never sum weight arrays or count raw records. Use
   `Microsimulation.calculate(var, year)` with microdf auto-weighting; the
   only weight ever referenced directly is `household_weight`
   (microplex-us#224).
3. **Donor-fit weighting (microplex-us#263):** the engine defaults donor fits
   to UNWEIGHTED even when the donor has survey weights
   (`ImputationStep.weights` is opt-in). For outcome-stratified donors like
   the PUF this is the eCPS "landmine" bug class (extreme low-weight donors
   broadcast as point masses, detonating under reweighting). Check #263's
   resolution before training on PUF or scoring candidates.

## Version floors

Engine requires Python ≥3.12 (microimpute's marker); the
microcalibrate-backed calibration path requires ≥3.13.
