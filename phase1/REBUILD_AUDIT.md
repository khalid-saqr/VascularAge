# Phase 1 rebuild audit

Phase 1 was rebuilt from merged Phase 0 after four external Colab failures exposed qualification-layer defects. No biological endpoint was executed in any failed run.

| External saved commit | Observed failure | Classification |
|---|---|---|
| `7b3cfbf7b4e3f735c2845c335e54e887e417f9c7` | runner failed but wrapper did not preserve sub-gate diagnostics | diagnostic design defect |
| `174a7454e430ef98c6a1cfe36965a6030c9b09d5` | unsupported NumPy-reference-via-JAX tie path selected a different tied index | numerical qualification design defect |
| `624d0f071eac5e60961f7d25562241187446ddcd` | Phase 1 incorrectly required contextual non-selected PWDB properties as columns in `pwdb_model_variations.csv` | source-contract category error |
| `d761948a914345bad9a0c54b330025c600dc72f3` | raw radial audit rejected canonical `NaN` missing/padding tokens | waveform-semantic category error |

## Rebuild rule

The rebuilt Phase 1 uses VascuQuest as the semantic authority for PWDB waveform missing/padding behavior and Tier-4 core validation. Raw-source code is retained only for two facts not fully established by Tier 4:

1. the exact six-factor `3^6` model-variation table;
2. an exhaustive, streaming audit of all 4,374 Radial-pressure rows using the **same blank/NaN missing and trailing-padding semantics implemented by VascuQuest**.

The rebuild does not modify any Phase-0 scientific hypothesis, primary endpoint, tolerance, observation arm, or falsification rule.

## Successful external qualification

The rebuilt notebook was subsequently executed in Google Colab with a T4 GPU and saved back to the branch. The executed notebook records:

- `PHASE 1 QUALIFICATION: PASS`;
- `PHASE 1 EXTERNAL QUALIFICATION CLEARED`;
- source qualification `PASS`;
- engine qualification `PASS`;
- `biological_endpoint_executed: false`;
- qualified VascularAge implementation commit `685ef575136ff0628ec2b598e914edce9cdd43e2`;
- pinned VascuQuest commit `79891036e61df3096536da8f647f2297b0d88252`;
- observed qualification-contract SHA-256 `18cc85b8e192b14acdfff7f08bd684704799e793b34bb558cfede0efbc5f0399`.

The executed-notebook evidence commit is intentionally preserved after the implementation commit because it proves which exact code revision was run externally. Squashing that evidence into a new code commit would weaken the direct correspondence between the notebook's recorded `vascularage_repo_commit` and the implementation that was actually executed.
