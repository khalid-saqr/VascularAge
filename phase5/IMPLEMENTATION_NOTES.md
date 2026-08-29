# Phase 5 / S2 implementation notes

This branch intentionally does **not** execute S2.

Scientific definitions are confined to the files covered by `S2_LOCK.json`. The Colab wrapper, notebook, validators, tests, checklist and output schema are orchestration/verification material and cannot alter the locked S2 operators.

Implementation invariants:

- Phase-4 A001 P0 artifacts are cryptographically verified before S2 is accepted.
- The preserved P0 `i,j` arrays define the authoritative 7,971,615-pair universe.
- The Phase-5 runner independently regenerates pair ordering and requires exact equality to P0.
- Radial duration differences are recomputed and required to match the preserved P0 duration array exactly; the preserved array is then used for adjudication.
- L1 is mean absolute pressure error, retaining mmHg units.
- L-infinity is maximum absolute pressure error, retaining mmHg units.
- Both use the unchanged 5 mmHg / 10 ms matched scales and `d <= 1` alias boundary.
- S2 No-Go is strictly conjunctive: both subject-set Jaccards must be `<0.50`.
- GPU float32 results are independently checked by a float64 boundary/control audit.
- CI tests only known-answer mathematics, lock integrity and runner guards; it never supplies `--execute-s2`.
