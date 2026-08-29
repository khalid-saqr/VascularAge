# Phase 4 — External Confirmatory Execution

Phase 4 is the first authorized execution of the prospectively locked biological trial.

## Original locked execution

The original Phase-3 scientific lock remains immutable:

- `phase3/LOCKED_TRIAL_CONFIG.json`
- `phase3/LOCK_MANIFEST.json`
- `src/vascularage/confirmatory.py`
- `src/vascularage/locked_io.py`
- `scripts/phase4_execute_locked.py`

Original protocol lock:

`89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963`

The first external run, preserved in `notebooks/04_confirmatory_trial.ipynb`, completed P0 and then stopped at P1 because the Phase-3 implementation incorrectly required Digital PPG raw active-sample counts to equal Radial-pressure raw active-sample counts. The preserved Drive evidence directory is:

`/MyDrive/VascularAge/phase_04/locked_trial_20260829T131721Z`

The P0 result is therefore already disclosed and must never be treated as prospectively unseen again.

## Protocol Amendment 001

A001 corrects only the over-constrained cross-site raw-sample equality assumption. It does not alter P0 or any downstream scientific tolerance/operator.

Authoritative amendment files:

- `phase4/AMENDMENT_001.md`
- `phase4/AMENDMENT_001_PROTOCOL.json`
- `phase4/AMENDMENT_001_LOCK.json`
- `src/vascularage/amendment001_io.py`
- `scripts/phase4_execute_amendment001.py`

Amendment-001 lock:

`1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7`

The refined rule is:

> No cross-signal raw-length equality is required unless a mathematical operation itself requires aligned source samples.

Consequently, ordinary secondary waveforms use their own valid active source support before 512-point phase resampling. Subject duration remains anchored to P0 Radial pressure. Reconstructed flow requires only local U/A alignment because `Q=U*A` is pointwise.

## Amendment-001 external execution workflow

Run:

`notebooks/04_confirmatory_trial_amendment001.ipynb`

The notebook and wrapper:

1. mount Google Drive and reuse the Phase-1-qualified PWDB/VascuQuest cache;
2. pin VascuQuest to `79891036e61df3096536da8f647f2297b0d88252`;
3. verify the original Phase-3 lock is still byte-identical;
4. verify the new A001 lock and all amended scientific-file hashes;
5. run repository tests;
6. require a non-CPU JAX backend;
7. verify canonical PWDB source checksums;
8. preserve and verify the original P0 evidence bundle by SHA-256;
9. audit all 52 common-site waveform members under the amended source semantics;
10. recompute P0 using the unchanged original P0 implementation;
11. run the float64 P0 numerical audit immediately after P0;
12. require the recomputed P0 outputs to reproduce the preserved original P0 evidence before any still-unseen endpoint can execute;
13. execute P1, P2, compensation, M1–M4 rescue, conventional benchmark and information geometry only after that gate passes;
14. write structured `execution_failure.json` evidence on any terminal exception;
15. persist the complete final evidence bundle to a new Drive directory without overwriting the first run.

## Evidence rule

The original failed executed notebook remains preserved. The A001 notebook starts unexecuted. After the external A001 run, the executed A001 notebook is saved back to the same branch and audited before Phase 4 can be cleared.

PR #7 remains draft until the amended full execution has passed all gates and the final output bundle has been independently audited.
