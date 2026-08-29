# Phase 5 / S2 — Post-Execution Audit

**Status:** externally executed and independently audited  
**Execution notebook:** `notebooks/05_s2_robustness.ipynb`  
**Saved Colab commit:** `9d02653d445e9aa215048dc82325d7df7d57f41f`  
**Scientific execution commit:** `b45ee69c423782aac06ef35391f9ccde1a23fe8f`  
**S2 lock:** `97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05`  
**Evidence folder:** `/MyDrive/VascularAge/phase_05/locked_trial_phase5_s2_20260829T162522Z`

## Execution provenance

The saved notebook records a GPU execution on `cuda:0`, with VascuQuest pinned to `79891036e61df3096536da8f647f2297b0d88252`. The run verified the preserved Phase-4 A001 evidence bundle before S2 computation.

Phase-4 evidence verification: **PASS**.  
Phase-4 P0 reproducibility gate carried forward: **PASS**.

## Locked S2 results

| Quantity | Result |
| --- | ---: |
| Subjects | 4,374 |
| Unordered cross-age pairs | 7,971,615 |
| P0 aliased subjects | 2,764 |
| L1 aliased subjects | 2,874 |
| L-infinity aliased subjects | 1,724 |
| Jaccard(L1, P0) | 0.9617258176757133 |
| Jaccard(L-infinity, P0) | 0.6237337192474675 |
| Locked threshold | 0.50 |
| `S2_NO_GO` | false |
| Locked adjudication | **PASS** |

The locked rule was `S2_NO_GO = (J_L1 < 0.50) AND (J_Linf < 0.50)`. It therefore does not fire.

## Independent artifact audit

The Drive bundle contains all required Phase-5 outputs. Independent SHA-256 calculation reproduced the bundle manifest exactly:

- `phase4_evidence_verification.json`: `2964ccd705fb0244c6df76e98048c0d9f2eab1385fac0d5cf93eb225ee94d35b`
- `s2_pair_components.npz`: `c6d9ee3a1e9673239aaaadb905154112e32da922964d05038dc723a372593f74`
- `s2_subject_results.csv`: `f289ada99d93e1a3d68b668f69a5b6f9a38dbaf2a470c82adf416da9e06df720`
- `s2_overlap_summary.json`: `6d48a3b597d32c3fd4ab1b20ccd73c2fc883467bcac93038db8fa3dbd8e1a35d`
- `s2_numerical_audit.json`: `fdc94c0f88bb1c84326b6c3e93625f3b6e1c18e04de3e1efd4c7587f4f5c05ce`
- `s2_summary.json`: `508ef535d2de47e324929d86a0d6145c461c35f08895749053f67a103bc09029`
- `execution_provenance.json`: `bc28b2cdf234385c672e4bea6caf2afd8ea3cd71346a032c71501b5fc13a6389`

Independent recomputation from `s2_pair_components.npz` reproduced exactly:

- L1 pair aliases: **92,848**
- L-infinity pair aliases: **3,310**
- L1 subject aliases: **2,874**
- L-infinity subject aliases: **1,724**
- `Jaccard(L1,P0) = 0.9617258176757133`
- `Jaccard(Linf,P0) = 0.6237337192474675`

The reconstructed subject sets agree exactly with all 4,374 rows of `s2_subject_results.csv`.

## Numerical audit

The locked float64 audit passed:

- boundary-sensitive pair rows: **6,950**
- deterministic control rows requested: **600**
- unique pair rows audited: **7,550**
- maximum absolute L1 distance difference: `2.0227349182277976e-06`
- maximum absolute L-infinity distance difference: `2.4742722573023457e-06`
- L1 classification changes: **0**
- L-infinity classification changes: **0**
- allowed distance difference: `1e-4`

## Interpretation note — not part of the locked adjudication

For a fixed pressure-difference vector, the sample-normalised metrics satisfy

`mean(|delta P|) <= RMSE(delta P) <= max(|delta P|)`.

Because all three arms use the same duration term and the same 5 mmHg / 10 ms scales, the subject alias sets must therefore be nested:

`A_Linf ⊆ A_P0 ⊆ A_L1`.

The observed results obey this exactly: all 2,764 P0-aliased subjects are L1-aliased, while all 1,724 L-infinity-aliased subjects are P0-aliased. L1 adds 110 subjects relative to P0; L-infinity removes 1,040.

A consequence identified during the post-execution audit is that, once Phase 4 had revealed `|A_P0| = 2,764`, the L1 Jaccard could no longer fall below 0.50: even if all 4,374 subjects were L1-aliased, `J(A_L1,A_P0) >= 2764/4374 = 0.6319158665`. Thus, under the prospectively locked two-arm `AND` rule, S2 was mathematically unable to trigger after the observed P0 alias fraction exceeded 50%.

This does **not** change the prospective S2 adjudication: S2 formally passes exactly as locked. It does mean the L1 half of S2 should not be presented as independent post-Phase-4 falsification evidence. The L-infinity result remains informative on its own and also exceeds the prespecified 0.50 agreement threshold (`0.6237337192`). No threshold or endpoint is changed retrospectively.

## Repository validation

After the executed notebook was saved, Phase-1, Phase-2, Phase-3, Phase-4 and Phase-5 CI all passed. Phase-5 CI accepted the notebook as a valid post-execution record while revalidating the lock and execution guard.
