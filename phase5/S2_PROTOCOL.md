# Phase 5 — S2 Robustness Analysis Lock

**Project:** The Locked In-Silico Trial Concept  
**Phase:** 5 — Prespecified robustness analysis  
**Endpoint:** S2 only  
**Execution status:** NOT EXECUTED

## 1. Purpose

Phase 5 evaluates the prospectively deferred S2 robustness rule from the Phase-3 lock. It does not redefine P0, alter the 5 mmHg / 10 ms reference scales, change the 7,971,615 cross-age pair universe, or introduce any subject-specific waveform normalisation.

The locked Phase-3 S2 rule is:

> `NO_GO_ROBUST_ALIASING_CLAIM` if **both** the L1-pressure and L-infinity-pressure subject-alias sets have Jaccard similarity `< 0.50` versus the P0 reference subject-alias set at matched 5 mmHg / 10 ms scales.

## 2. Reference evidence

S2 is anchored to the externally executed Phase-4 Amendment-001 evidence bundle:

`locked_trial_amendment001_20260829T153743Z`

The Phase-5 runner must verify the cryptographic hashes of the preserved P0 pair components and P0 subject results before any S2 endpoint is accepted.

## 3. Pressure metrics

The source observation remains the same 512-point phase-resampled **Radial pressure** in absolute mmHg, with duration anchored to the Radial active source support.

For a cross-age pair `(i,j)` with phase pressure samples `P_i(k), P_j(k)`, `k=1,...,512`:

### L1 pressure discrepancy

The operational L1 pressure discrepancy is the **sample-normalised discrete L1 norm**, equivalently mean absolute pressure error:

`DeltaP_L1 = mean_k |P_i(k) - P_j(k)|`

This quantity remains in mmHg and is therefore dimensionally compatible with the prospectively locked 5 mmHg pressure scale. A raw unnormalised sum is forbidden because it would carry mmHg-sample units and would not be commensurate with the locked 5 mmHg scale.

### L-infinity pressure discrepancy

`DeltaP_Linf = max_k |P_i(k) - P_j(k)|`

This quantity is also in mmHg.

## 4. Matched S2 distances

For each original P0 cross-age pair, using the same absolute Radial duration difference `DeltaT`:

`d_L1 = sqrt((DeltaP_L1 / 5 mmHg)^2 + (DeltaT / 10 ms)^2)`

`d_Linf = sqrt((DeltaP_Linf / 5 mmHg)^2 + (DeltaT / 10 ms)^2)`

A pair aliases under a metric when its matched distance is `<= 1`.

No new tolerance grid is introduced in Phase 5.

## 5. Subject-level alias sets

Let:

- `A_P0` = subjects with at least one P0 reference alias;
- `A_L1` = subjects with at least one L1-pressure alias;
- `A_Linf` = subjects with at least one L-infinity-pressure alias.

The two primary Phase-5 statistics are:

`J_L1 = Jaccard(A_L1, A_P0)`

`J_Linf = Jaccard(A_Linf, A_P0)`

## 6. S2 adjudication

The prospective rule is applied literally:

`S2_NO_GO = (J_L1 < 0.50) AND (J_Linf < 0.50)`

Therefore one alternative metric retaining Jaccard `>= 0.50` is sufficient for S2 not to trigger. Phase 5 must report both Jaccards and both subject-set cardinalities regardless of the adjudication.

No post-result threshold modification is allowed.

## 7. Numerical execution

Production pairwise L1 and L-infinity calculations use JAX/XLA float32 on a non-CPU accelerator and preserve the original age-pair block ordering.

The preserved Phase-4 `i`, `j`, and `duration_diff_ms` arrays are the authoritative pair universe. The Phase-5 runner must reproduce the same `i,j` ordering and must use the preserved duration component.

A float64 audit independently recomputes every pair whose float32 S2 distance lies within `0.01` of the alias boundary for either alternative metric, plus a deterministic control sample of 600 pair rows. The run is invalid if:

- any audited alias classification changes between float32 and float64; or
- the maximum absolute audited distance discrepancy exceeds `1e-4`.

## 8. Output contract

A successful S2 execution emits:

- `phase4_evidence_verification.json`
- `s2_pair_components.npz`
- `s2_subject_results.csv`
- `s2_overlap_summary.json`
- `s2_numerical_audit.json`
- `s2_summary.json`
- `execution_provenance.json`

The Colab wrapper additionally emits:

- `source_preflight.json`
- `bundle_hashes.json`
- `external_execution_evidence.json`
- `phase5_console.log`

## 9. Change control

This Phase-5 lock operationalises the already named L1 and L-infinity robustness metrics without changing the prospective S2 threshold or P0 definition.

After this lock is committed, any change to the metric definitions, pressure/duration scales, alias boundary, Jaccard threshold, Boolean adjudication, reference P0 hashes, or pair universe requires a numbered Phase-5 amendment before execution.

The Google Colab notebook is an execution shell only. It may install dependencies, verify commits/locks, invoke the guarded runner, persist evidence, and display terminal results; it may not contain an alternative scientific implementation.
