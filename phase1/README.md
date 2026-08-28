# Phase 1 — Rebuilt external Colab qualification

**Status: CLEARED after external Google Colab execution.**

This phase qualifies the canonical PWDB/VascuQuest source boundary and the synthetic JAX numerical engine **without executing any biological cross-age endpoint**.

External execution evidence is preserved in `notebooks/01_engine_qualification.ipynb` on this branch. The successful run was executed on Google Colab with a T4 GPU and recorded:

- `PHASE 1 QUALIFICATION: PASS`
- `PHASE 1 EXTERNAL QUALIFICATION CLEARED`
- `source_qualification: PASS`
- `engine_qualification: PASS`
- `biological_endpoint_executed: false`
- qualified VascularAge implementation commit: `685ef575136ff0628ec2b598e914edce9cdd43e2`
- pinned VascuQuest commit: `79891036e61df3096536da8f647f2297b0d88252`
- observed qualification-contract SHA-256: `18cc85b8e192b14acdfff7f08bd684704799e793b34bb558cfede0efbc5f0399`

Persistent storage used during execution: `/content/drive/MyDrive/VascularAge/phase_01`.

The qualification bundle was written under `qualification_v2/` in Google Drive. Raw PWDB artifacts remain outside Git.

## Qualified boundary

Phase 1 established:

- VascuQuest Tier-4 real-source validation PASS;
- canonical `pwdb_model_variations.csv` checksum and exact eight-column schema;
- 4,374 source identities and six age groups of 729;
- complete six-factor `3^6 = 729` design at every age and age alignment with model configurations;
- all 4,374 Radial-pressure rows aligned;
- canonical blank/`NaN` trailing-padding semantics accepted and zero internal missing Radial-pressure samples required;
- boundary-subject Radial pressure cross-checks against VascuQuest masks, `mmHg` units, and `SOURCE` evidence;
- synthetic JAX/NumPy known-answer and equivalence tests;
- runtime/environment/provenance recording;
- no real-PWDB cross-age aliasing, separability, compensation, or measurement-rescue endpoint calculated.

Phase 1 does **not** authorize Phase 4 biological execution. Phase 2 and Phase 3 must still be completed and merged first.
