# Phase 5 — S2 robustness

Phase 5 executes only the prospectively deferred **S2 robustness** endpoint from the Phase-3 lock.

The scientific implementation is frozen by:

`97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05`

The endpoint compares the preserved P0 subject-alias set with matched-scale alternative pressure metrics:

- L1 pressure = mean absolute pressure error over the same 512 phase points;
- L-infinity pressure = maximum absolute pressure error over the same 512 phase points.

Both use the unchanged 5 mmHg pressure scale, unchanged 10 ms Radial-duration scale, unchanged cross-age pair universe, and unchanged alias boundary `d <= 1`.

S2 triggers `NO_GO_ROBUST_ALIASING_CLAIM` only when **both** alternative subject-set Jaccards versus P0 are `<0.50`.

No Phase-5 biological endpoint is executed by repository CI. Real execution is guarded by `--execute-s2` and is intended to occur externally in `notebooks/05_s2_robustness.ipynb` on a non-CPU Colab runtime. Phase-4 evidence is read from its preserved A001 Drive folder; Phase-5 outputs are written separately under `/MyDrive/VascularAge/phase_05/`.
