# VascularAge

**Is Arterial Age Identifiable From the Pulse?**  
*An Exhaustive In-Silico Trial of Physiological Aliasing and Measurement Rescue in 4,374 Virtual Subjects*

This repository implements **The Locked In-Silico Trial Concept**: a prospectively specified computational experiment asking whether distinct age-conditioned cardiovascular states can generate experimentally indistinguishable arterial pulse phenotypes, which physiological perturbations create those aliases, and which complementary measurements restore identifiability.

The trial uses the Pulse Wave DataBase (PWDB) through VascuQuest and is designed for reproducible execution with JAX/XLA and Google Colab persistent storage.

## Phase status

- **Phase 0 — Canonical Trial Specification:** merged and frozen.
- **Phase 1 — Computational Engine and Source Qualification:** external Google Colab qualification **PASS**; awaiting manual PR review/merge.
- **Phase 2 — Systematic Evidence Map:** not started.
- **Phase 3 — Prospective Protocol Lock:** not started.
- **Phase 4 — Full in-silico trial:** prohibited until Phases 2 and 3 are completed and merged.

Phase 1 qualified the canonical PWDB/VascuQuest source boundary and the synthetic JAX engine without calculating any real cross-age biological endpoint. The executed notebook and qualification provenance are preserved on the Phase-1 branch.

## Scientific boundary

The primary trial population is the complete PWDB factorial design:

- 4,374 virtual haemodynamic simulation instances;
- six model ages;
- 729 configurations per age;
- six controlled coordinates: HR, SV, LVET, DIA, PWV, and MAP (source column `MBP`).

The primary biological analysis remains locked for Phase 4. No cross-age aliasing result, age-identifiability surface, compensation vector, or biological measurement-rescue result has yet been calculated.
