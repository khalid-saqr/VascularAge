# Phase 5 — S2 Robustness

Phase 5 closes the prospectively deferred **S2 robustness** endpoint from the Phase-3 lock.

Scientific lock:

`97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05`

The endpoint compares the preserved P0 subject-alias set with matched-scale alternative pressure metrics:

- L1 pressure = mean absolute pressure error over the same 512 phase points;
- Linf pressure = maximum absolute pressure error over the same 512 phase points.

Both retain the 5 mmHg pressure scale, 10 ms Radial-duration scale, complete cross-age pair universe, and alias boundary `d <= 1`.

The prospectively locked no-go rule was:

```text
Jaccard(A_L1, A_P0) < 0.50
AND
Jaccard(A_Linf, A_P0) < 0.50
```

## Final execution status

**EXECUTED, INDEPENDENTLY AUDITED, AND PASSED.**

Executed notebook: `notebooks/05_s2_robustness.ipynb`

Preserved evidence directory:

`/MyDrive/VascularAge/phase_05/locked_trial_phase5_s2_20260829T162522Z`

| Metric | Alias subjects | Jaccard vs P0 |
|---|---:|---:|
| P0 / RMSE | 2,764 | 1.0000000000 |
| L1 / MAE | 2,874 | **0.9617258177** |
| Linf / maximum error | 1,724 | **0.6237337192** |

`S2_NO_GO = false`; adjudication: **PASS**.

The numerical audit passed with zero classification changes in the audited boundary/control rows. Phase-4 source hashes and the P0 reproducibility gate also reverified before S2 execution.

## Interpretation note

For any fixed 512-point pressure-difference vector,

```text
mean(abs(delta P)) <= RMSE(delta P) <= max(abs(delta P))
```

With the same pressure/duration scales, this implies `A_Linf ⊆ A_P0 ⊆ A_L1` at subject-set level. After the observed P0 alias prevalence was known, the L1 arm could not independently cause the prospectively locked two-arm AND rule to fail. This does **not** alter the formal prospective S2 PASS; it is recorded as a post-execution interpretation limitation. The Linf arm remained independently informative and exceeded the locked `0.50` threshold.

See `POST_EXECUTION_AUDIT.md` for the complete audit record.
