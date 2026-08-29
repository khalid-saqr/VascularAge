# Phase 4 — External Confirmatory Execution

Phase 4 is the first authorized execution of the prospectively locked biological trial.

The scientific implementation is **not redefined here**. The authoritative analysis remains the Phase-3 lock package:

- `phase3/LOCKED_TRIAL_CONFIG.json`
- `phase3/LOCK_MANIFEST.json`
- `src/vascularage/confirmatory.py`
- `src/vascularage/locked_io.py`
- `scripts/phase4_execute_locked.py`

Protocol lock:

`89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963`

## External execution workflow

The confirmatory trial is executed in Google Colab through:

`notebooks/04_confirmatory_trial.ipynb`

The notebook:

1. mounts Google Drive;
2. reuses the persistent Phase-1-qualified PWDB/VascuQuest cache;
3. clones this Phase-4 branch and pins VascuQuest to `79891036e61df3096536da8f647f2297b0d88252`;
4. verifies every Phase-3 locked-file SHA and the aggregate lock digest;
5. runs the repository tests;
6. requires a non-CPU JAX backend;
7. verifies checksums for the exact PWDB artifacts required by the locked runner;
8. invokes `scripts/phase4_execute_locked.py` with `--execute-locked-trial` and the exact lock SHA;
9. emits one-minute heartbeats while the locked process is running;
10. validates all 14 locked output artifacts and the float64 numerical audit;
11. writes bundle hashes and external execution evidence to Google Drive.

## Evidence rule

The initial Phase-4 PR contains an **unexecuted** notebook only.

After external execution, the user saves the executed notebook back to the same branch and path. The saved notebook is then audited against the unexecuted source before Phase 4 is cleared.

No Phase-3 scientific parameter may be changed in this phase.
