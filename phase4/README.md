# Phase 4 — Confirmatory Execution

Phase 4 contains the externally executed confirmatory biological trial and the prospective Amendment 001 required to complete it.

## Original locked execution

The original Phase-3 scientific lock remains immutable:

`89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963`

The first external run, preserved in `notebooks/04_confirmatory_trial.ipynb`, completed P0 and then stopped at P1 because the locked implementation incorrectly required Digital-PPG raw active-sample counts to equal Radial-pressure raw active-sample counts.

That failed run is retained as provenance. Its disclosed P0 result was subsequently required to reproduce exactly before any still-unseen endpoint could execute.

## Amendment 001

A001 corrected only the over-constrained cross-site raw-sample equality assumption. It did not change P0 or any scientific tolerance/operator.

Authoritative files:

- `AMENDMENT_001.md`
- `AMENDMENT_001_PROTOCOL.json`
- `AMENDMENT_001_LOCK.json`
- `../src/vascularage/amendment001_io.py`
- `../scripts/phase4_execute_amendment001.py`

Amendment lock:

`1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7`

The amended rule is:

> No cross-signal raw-length equality is required unless a mathematical operation itself requires aligned source samples.

The executed Amendment-001 notebook is retained at `notebooks/04_confirmatory_trial_amendment001.ipynb`.

## Final execution status

**EXECUTED AND AUDITED.**

Preserved evidence directory:

`/MyDrive/VascularAge/phase_04/locked_trial_amendment001_20260829T153743Z`

Key confirmatory results at the P0 reference tolerance:

- P0 pair aliases: **53,842**
- P0 alias subjects: **2,764 / 4,374**
- subject alias fraction: **0.6319158664837677**
- P1 Digital-PPG alias fraction: **0.659122085048011**
- P2 Carotid-pressure alias fraction: **0.6506630086877**
- M1 rescue fraction: **0.4283646888567294**
- M2/M3/M4 rescue fraction: **1.0**
- compensation top-20 concentration: **0.5821273516642547**
- locked compensation-null 95th percentile: **0.033646888567293774**
- canonical `S4_no_go`: **false**

Phase 4 also produced the preserved pair-component table used by the Phase-5 and Phase-5B robustness closures.

The failed original notebook, the successful amended notebook, the original protocol lock, and Amendment 001 are all retained deliberately as the auditable execution history.
