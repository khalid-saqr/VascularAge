# Phase 5B — Compensation Tie-Sensitivity Closure

## Purpose

Phase 3 prospectively required a Phase-5 sensitivity analysis over **co-nearest alternatives** for the compensation-motif analysis. Phase 4 used the locked canonical rule: among targets within `min_distance + 1e-6`, choose the smallest global target row index.

Phase 5B closes that obligation without re-running PWDB waveforms or creating a new biological endpoint. It operates only on the preserved Phase-4 evidence bundle `locked_trial_amendment001_20260829T153743Z`.

## Fixed source evidence

Phase 5B is anchored to:

- current merged `main`: `dd64cf00699ade42ba4505ddc6f0ffa20a982894`
- original Phase-3 lock: `89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963`
- Amendment 001 lock: `1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7`
- Phase-5/S2 lock: `97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05`
- the exact Phase-4 hashes listed in `TIE_SENSITIVITY_SPEC.json`

The critical preserved artifacts are:

- `primary_pair_components.npz`
- `primary_subject_results.csv`
- `compensation_vectors.csv`
- `compensation_motifs.csv`
- `compensation_null_summary.json`

No waveform file, PWDB source archive, VascuQuest checkout, GPU backend, random generator, or new simulation is permitted.

## Co-nearest set

For subject `s`, let the preserved Phase-4 reference distance to a cross-age target `t` be

`D(s,t) = sqrt((pressure_rmse_mmHg/5)^2 + (duration_diff_ms/10)^2)`.

The Phase-3 tie tolerance remains exactly `1e-6`.

The co-nearest target set is

`C_s = {t : age_t != age_s and D(s,t) <= min_u D(s,u) + 1e-6}`.

The compensation analysis only uses P0-reference-aliased source subjects, so that set is the primary Phase-5B scope. An all-4,374-subject tie diagnostic is also reported.

## Closure rule

Phase 5B **PASSes** only if all of the following hold:

1. every required Phase-4 artifact matches its locked SHA-256;
2. the complete 7,971,615-pair universe is present;
3. reconstructed nearest distance, canonical target, tie count, and P0 alias class agree with all 4,374 preserved Phase-4 subject rows;
4. every P0-reference-aliased source has `|C_s| = 1`;
5. all preserved compensation source-target rows use that reconstructed unique target;
6. the top-20 motif concentration independently recomputes to the preserved canonical Phase-4 value.

If any P0-reference-aliased source has `|C_s| > 1`, Phase 5B **STOPs**. No averaging, weighting, randomisation, best-case, worst-case, enumeration policy, or other retrospective aggregation rule may be invented after observing the tie structure.

## Interpretation of a PASS

When every P0-reference-aliased source has a singleton co-nearest set, the tie-sensitivity perturbation has zero degrees of freedom. Therefore the co-nearest-sensitive compensation vectors and motif concentration are necessarily identical to the canonical Phase-4 result.

This closure does **not**:

- rerun or replace S4;
- create a new S4 threshold;
- regenerate the locked permutation null;
- modify the canonical Phase-4 result;
- change any Phase-3 or Amendment 001 scientific definition.

It only establishes whether the canonical smallest-index rule had any actual biological choice to resolve.

## Expected preserved canonical reference

The preserved Phase-4 values bound into this closure are:

- P0-reference-aliased sources: `2,764`
- canonical top-20 motif concentration: `0.5821273516642547`
- locked null 95th percentile: `0.033646888567293774`
- locked null permutations: `2,000`
- canonical `S4_no_go`: `false`

These are verification targets, not parameters to be refit.

## Execution and evidence

The guarded runner is `scripts/phase5b_tie_closure.py`. It requires the explicit flag `--execute-tie-closure`.

The Colab shell is `notebooks/06_tie_sensitivity_closure.ipynb`. It is intentionally CPU-only and reads the preserved Phase-4 Drive directory. A successful execution writes a timestamped evidence bundle under:

`/content/drive/MyDrive/VascularAge/phase_05b/locked_trial_phase5b_tie_closure_<UTCSTAMP>`

and terminates with:

`PHASE 5B TIE-SENSITIVITY CLOSURE: PASS`

`PHASE 5B CLOSURE: COMPLETE`

The executed notebook must then be saved back to the Phase-5B branch before final evidence audit and merge.
