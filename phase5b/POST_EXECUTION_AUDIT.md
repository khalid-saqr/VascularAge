# Phase 5B — Post-Execution Audit

This document is an **audit record outside the locked Phase-5B scientific package**. It does not modify the Phase-5B rule, thresholds, source evidence, or lock digest.

## Execution identity

- Phase-5B tie-sensitivity lock: `6b9f11bf0c662c8263e531b0440882881d79b5ab70aaa4aaeffd4e4a69d741c2`
- Parent merged `main`: `dd64cf00699ade42ba4505ddc6f0ffa20a982894`
- Scientific execution commit cloned by Colab: `2f38433078342f8418a480fce027341413ac8a8a`
- Saved executed-notebook commit: `48b3709f8efa592f02e1124ae39a991839791410`
- Saved executed-notebook blob SHA: `e998bbb8e6037c0ddb6e13b7a492d2bd459c01fb`
- Preserved Phase-4 evidence root: `locked_trial_amendment001_20260829T153743Z`
- Phase-5B evidence root: `locked_trial_phase5b_tie_closure_20260829T171647Z`
- Execution class: evidence-only CPU
- No PWDB waveform or VascuQuest access; no randomness; no new null distribution.

The Colab save commit changes only `notebooks/06_tie_sensitivity_closure.ipynb`. Its source cells are unchanged from the locked pre-execution notebook; only Colab metadata, execution counts, and outputs were added. The notebook records all three required terminal markers:

- `PHASE 5B TIE-SENSITIVITY CLOSURE: PASS`
- `PHASE 5B CLOSURE: COMPLETE`
- `PHASE 5B NOTEBOOK: SUCCESS`

## Executed closure result

| Quantity | Result |
| --- | ---: |
| Subjects | 4,374 |
| Unordered cross-age pairs | 7,971,615 |
| Locked tie tolerance | `1e-6` |
| P0-reference-aliased sources | 2,764 |
| Subjects with co-nearest alternatives, all subjects | **0** |
| P0-aliased sources with co-nearest alternatives | **0** |
| Maximum co-nearest count, all subjects | **1** |
| Maximum co-nearest count, P0 aliases | **1** |
| Minimum nearest/second-nearest gap, all subjects | `1.4781951904296875e-05` |
| Minimum nearest/second-nearest gap, P0 aliases | `4.976987838745117e-05` |
| Canonical top-20 motif concentration | `0.5821273516642547` |
| Co-nearest-sensitive top-20 concentration | `0.5821273516642547` |
| Difference | **0.0** |
| Locked null 95th percentile | `0.033646888567293774` |
| S4 reopened | **false** |
| Outcome | **NO_CO_NEAREST_ALTERNATIVES** |
| Closure adjudication | **PASS** |

Because every P0-aliased source has a singleton co-nearest set, the prospectively required tie-sensitivity perturbation has zero degrees of freedom. The canonical smallest-index rule did not resolve any actual tie among the sources entering the compensation analysis. No alternative weighting or aggregation rule is therefore required or introduced.

## Phase-5B evidence-bundle SHA-256 audit

Independent SHA-256 calculation reproduced `bundle_hashes.json` exactly:

- `canonical_compensation_verification.json`: `8b17b955ff16d78a718dc1b34a463e95e35fb89298a50cfb827765ca4e252c16`
- `execution_provenance.json`: `0234e40910e60fd2dfdb90dbf354d09e01e1d0532e239053994bdb8087db0aae`
- `phase4_evidence_verification.json`: `234dd6302efe42860a3300d4e8ae964c6c391d88482df06a8a56387cf5d6d825`
- `tie_sensitivity_summary.json`: `a612f9f288a816e0262264655083f2a3a8eadf024f3cf70edd7ecd1c850ea4c7`
- `tie_subject_audit.csv`: `0e978d3460432ea2e8b947734c9c09ba8b2b41efe3a426394e9b4c3849827885`

## Reverification of bound Phase-4 artifacts

The five Phase-4 artifacts bound into Phase 5B independently match their locked hashes:

- `primary_pair_components.npz`: `f4e411dab367bf758466c89d65dcf261b2518af6fbd718b83eae9c2e021184bf`
- `primary_subject_results.csv`: `aa20eb842496e8ad3bb85232bafff18ba4724903f76f1e79e6b1ff3da036829a`
- `compensation_vectors.csv`: `f350008a80b594333dfd6a6391144f8962df71cffd6b4ac283a58f29d23b4472`
- `compensation_motifs.csv`: `fd52a339065ba394203ca886474b15e12fe70340ba3e451f1ecd253333f1cd79`
- `compensation_null_summary.json`: `891283d13343c7147254758af7cb7280fe4f2243056c5d62cadb5e978c8efa30`

The original Phase-3 lock and Amendment 001 lock also remain exact in `phase4_evidence_verification.json`.

## Independent reconstruction from the complete pair table

The audit independently loaded the preserved `primary_pair_components.npz` and reconstructed the Phase-4 reference distance in float32 exactly as the locked production analysis:

`D = sqrt((pressure_rmse_mmHg / 5)^2 + (duration_diff_ms / 10)^2)`.

For every one of the 4,374 subjects the audit recomputed the minimum cross-age distance, canonical target, co-nearest count at `1e-6`, second-nearest distance outside the tie window, and P0 alias class.

The reconstruction produced:

- P0 alias sources: **2,764**;
- all-subject co-nearest alternatives: **0**;
- P0-alias co-nearest alternatives: **0**;
- maximum tie count: **1** for both scopes;
- minimum all-subject nearest/second-nearest gap: `1.4781951904296875e-05`;
- minimum P0-alias gap: `4.976987838745117e-05`.

All reconstructed canonical targets, tie counts, and alias labels agree exactly with all 4,374 rows in `primary_subject_results.csv`. Reconstructed distances agree to floating serialization precision. The independently reconstructed arrays also agree exactly with all 4,374 rows in the emitted `tie_subject_audit.csv`.

## Independent compensation verification

The preserved compensation table contains exactly 2,764 rows. Independently:

- the source IDs are exactly the reconstructed P0-aliased source set;
- every target ID is exactly the reconstructed unique nearest target;
- the six-dimensional compensation vectors yield exactly **178** distinct motifs;
- every motif/count pair in `compensation_motifs.csv` is reproduced exactly;
- total motif count is **2,764**;
- top-20 motif count is **1,609**;
- `1609 / 2764 = 0.5821273516642547` exactly at reported precision.

The preserved `compensation_null_summary.json` remains:

- observed top-20 concentration `0.5821273516642547`;
- null 95th percentile `0.033646888567293774`;
- permutations `2000`;
- `S4_no_go = false`.

Phase 5B does not rerun this null and does not create a new S4 adjudication.

## CI

After the executed notebook was saved at `48b3709f8efa592f02e1124ae39a991839791410`, all six PR-head workflows passed:

- Phase 1 rebuild qualification CI;
- Phase 2 evidence-map CI;
- Phase 3 protocol-lock CI;
- Phase 4 external execution notebook CI;
- Phase 5 S2 protocol-lock CI;
- Phase 5B tie-sensitivity closure CI.

Phase-5B CI accepted the executed notebook as a valid post-execution record while revalidating the Phase-5B lock, repository tests, notebook source signature, and guarded execution semantics.

## Audit conclusion

**PHASE 5B / COMPENSATION TIE-SENSITIVITY CLOSURE IS EXECUTED, INDEPENDENTLY AUDITED, AND PASSED.**

The prospectively required co-nearest-target sensitivity obligation is therefore closed without modifying or reopening the canonical Phase-4 S4 result.
