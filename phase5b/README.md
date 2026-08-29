# Phase 5B — Tie-Sensitivity Closure

Phase 5B closes the final prospective obligation in the Phase-3 compensation analysis: repeat the motif interpretation over admissible co-nearest targets within the locked nearest-target tolerance `1e-6`.

Scientific lock:

`6b9f11bf0c662c8263e531b0440882881d79b5ab70aaa4aaeffd4e4a69d741c2`

The closure is evidence-only. It reads the preserved Phase-4 pair/component and compensation artifacts; it does not access PWDB waveforms, VascuQuest, a GPU, or a random generator.

## Final execution status

**EXECUTED, INDEPENDENTLY AUDITED, AND PASSED.**

Executed notebook: `notebooks/06_tie_sensitivity_closure.ipynb`

Preserved evidence directory:

`/MyDrive/VascularAge/phase_05b/locked_trial_phase5b_tie_closure_20260829T171647Z`

| Quantity | Result |
|---|---:|
| Subjects | 4,374 |
| P0-reference-aliased sources | 2,764 |
| Subjects with co-nearest alternatives | **0** |
| P0 aliases with co-nearest alternatives | **0** |
| Maximum co-nearest count | **1** |
| Minimum nearest/second gap, all | `1.4781951904296875e-05` |
| Minimum nearest/second gap, P0 aliases | `4.976987838745117e-05` |
| Canonical top-20 motif concentration | `0.5821273516642547` |
| Co-nearest-sensitive top-20 concentration | `0.5821273516642547` |
| Difference | **0.0** |
| Outcome | **NO_CO_NEAREST_ALTERNATIVES** |
| Closure adjudication | **PASS** |

The canonical smallest-index rule therefore resolved no actual tie among the compensation sources. Phase 5B did not reopen S4, generate a new null distribution, or change any prospective criterion.

Authoritative locked files remain `TIE_SENSITIVITY_CLOSURE.md`, `TIE_SENSITIVITY_SPEC.json`, and `TIE_SENSITIVITY_LOCK.json`. The final external audit is recorded separately in `POST_EXECUTION_AUDIT.md`.
