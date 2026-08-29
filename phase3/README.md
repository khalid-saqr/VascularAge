# Phase 3 — Prospective Protocol Lock

Phase 3 freezes the exact confirmatory design and executable analysis primitives for **The Locked In-Silico Trial Concept**.

No biological endpoint is executed in this phase.

The lock package contains:
- `LOCKED_TRIAL_CONFIG.json` — complete machine-readable analysis configuration;
- `ANALYSIS_PLAN.md` — human-readable confirmatory protocol;
- `NOVELTY_BOUNDARY.md` — Phase-2 novelty claim boundary;
- `LOCK_MANIFEST.json` — cryptographic lock manifest and upstream provenance;
- `LOCKED_OUTPUT_SCHEMA.json` — required Phase-4 output inventory;
- `src/vascularage/confirmatory.py` — frozen mathematical analysis primitives;
- `src/vascularage/locked_io.py` — frozen qualified PWDB preparation semantics;
- `scripts/phase4_execute_locked.py` — guarded confirmatory runner, committed but not executed in Phase 3;
- Phase-3 tests and CI.

Phase 4 is authorized only after this PR is manually merged. Phase 4 may orchestrate the locked runner and persist outputs; it may not modify locked scientific parameters.
