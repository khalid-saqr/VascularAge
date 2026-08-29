# Phase 5B — Post-Execution Audit

This document is an **audit record outside the locked Phase-5B scientific package**. It does not modify the Phase-5B rule, thresholds, source evidence, or lock digest.

## Execution identity

- Phase-5B tie-sensitivity lock: `6b9f11bf0c662c8263e531b0440882881d79b5ab70aaa4aaeffd4e4a69d741c2`
- Parent merged `main` used by the lock: `dd64cf00699ade42ba4505ddc6f0ffa20a982894`
- Scientific execution commit cloned by Colab: `2f38433078342f8418a480fce027341413ac8a8a`
- Saved executed-notebook commit: `48b3709f8efa592f02e1124ae39a991839791410`
- Saved executed-notebook blob SHA: `e998bbb8e6037c0ddb6e13b7a492d2bd459c01fb`
- Preserved Phase-4 evidence root: `locked_trial_amendment001_20260829T153743Z`
- Phase-5B evidence root: `locked_trial_phase5b_tie_closure_20260829T171647Z`
- Execution class: evidence-only CPU
- No PWDB waveform or VascuQuest access; no randomness; no new null distribution.

The Colab save commit changed only `notebooks/06_tie_sensitivity_closure.ipynb`. Source cells were unchanged from the locked pre-execution notebook; Colab added metadata, execution counts, and outputs.

Terminal execution markers:

- `PHASE 5B TIE-SENSITIVITY CLOSURE: PASS`
- `PHASE 5B CLOSURE: COMPLETE`
- `PHASE 5B NOTEBOOK: SUCCESS`

## Executed closure result

| Quantity | Result |
|---|---:|
| Subjects | 4,374 |
| Unordered cross-age pairs | 7,971,615 |
| Locked tie tolerance | `1e-6` |
| P0-reference-aliased sources | 2,764 |
| Subjects with co-nearest alternatives, all | **0** |
| P0 aliases with co-nearest alternatives | **0** |
| Maximum co-nearest count, all | **1** |
| Maximum co-nearest count, P0 aliases | **1** |
| Minimum nearest/second-nearest gap, all | `1.4781951904296875e-05` |
| Minimum gap, P0 aliases | `4.976987838745117e-05` |
| Canonical top-20 motif concentration | `0.5821273516642547` |
| Co-nearest-sensitive top-20 concentration | `0.5821273516642547` |
| Difference | **0.0** |
| Locked null 95th percentile | `0.033646888567293774` |
| S4 reopened | **false** |
| Outcome | **NO_CO_NEAREST_ALTERNATIVES** |
| Closure adjudication | **PASS** |

Because every P0-aliased source has a singleton co-nearest set, the prospectively required tie-sensitivity perturbation has zero degrees of freedom. The canonical smallest-index rule did not resolve any actual tie among the sources entering the compensation analysis.

## Phase-5B evidence-bundle SHA-256 audit

Independent SHA-256 calculation reproduced `bundle_hashes.json` exactly:

- `canonical_compensation_verification.json`: `8b17b955ff16d78a718dc1b34a463e95e35fb89298a50cfb827765ca4e252c16`
- `execution_provenance.json`: `0234e40910e60fd2dfdb90dbf354d09e01e1d0532e239053994bdb8087db0aae`
- `phase4_evidence_verification.json`: `234dd6302efe42860a3300d4e8ae964c6c391d88482df06a8a56387cf5d6d825`
- `tie_sensitivity_summary.json`: `a612f9f288a816e0262264655083f2a3a8eadf024f3cf70edd7ecd1c850ea4c7`
- `tie_subject_audit.csv`: `0e978d3460432ea2e8b947734c9c09ba8b2b41efe3a426394e9b4c3849827885`

## Reverification of bound Phase-4 artifacts

The five Phase-4 artifacts bound into Phase 5B independently matched their locked hashes:

- `primary_pair_components.npz`: `f4e411dab367bf758466c89d65dcf261b2518af6fbd718b83eae9c2e021184bf`
- `primary_subject_results.csv`: `aa20eb842496e8ad3bb85232bafff18ba4724903f76f1e79e6b1ff3da036829a`
- `compensation_vectors.csv`: `f350008a80b594333dfd6a6391144f8962df71cffd6b4ac283a58f29d23b4472`
- `compensation_motifs.csv`: `fd52a339065ba394203ca886474b15e12fe70340ba3e451f1ecd253333f1cd79`
- `compensation_null_summary.json`: `891283d13343c7147254758af7cb7280fe4f2243056c5d62cadb5e978c8efa30`

The original Phase-3 and Amendment-001 lock identities also reverified.

## Independent reconstruction

The audit independently loaded `primary_pair_components.npz` and reconstructed the Phase-4 reference distance in float32 production arithmetic:

```text
D = sqrt((pressure_rmse_mmHg / 5)^2 + (duration_diff_ms / 10)^2)
```

For all 4,374 subjects it reproduced the minimum cross-age distance, canonical target, co-nearest count at `1e-6`, second-nearest distance outside the tie window, and P0 alias class.

Results:

- P0 alias sources: **2,764**
- all-subject co-nearest alternatives: **0**
- P0-alias co-nearest alternatives: **0**
- maximum tie count: **1**
- minimum all-subject nearest/second gap: `1.4781951904296875e-05`
- minimum P0-alias gap: `4.976987838745117e-05`

All reconstructed canonical targets, tie counts, alias labels, and emitted `tie_subject_audit.csv` rows agreed.

## Independent compensation verification

The preserved compensation table contains exactly 2,764 rows. The audit independently reproduced:

- the complete P0-aliased source set;
- every canonical target ID;
- **178** distinct six-dimensional compensation motifs;
- every motif/count pair in `compensation_motifs.csv`;
- total motif count **2,764**;
- top-20 motif count **1,609**;
- `1609 / 2764 = 0.5821273516642547`.

The preserved null remains:

- observed top-20 concentration `0.5821273516642547`;
- null 95th percentile `0.033646888567293774`;
- permutations `2000`;
- `S4_no_go = false`.

Phase 5B did not rerun this null and did not create a new S4 adjudication.

## Conclusion

**PHASE 5B / COMPENSATION TIE-SENSITIVITY CLOSURE IS EXECUTED, INDEPENDENTLY AUDITED, AND PASSED.**

The prospectively required co-nearest-target sensitivity obligation is closed without modifying or reopening the canonical Phase-4 S4 result.
