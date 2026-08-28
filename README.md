# VascularAge

**The Locked In-Silico Trial Concept**

*Is Arterial Age Identifiable From the Pulse? An Exhaustive In-Silico Trial of Physiological Aliasing and Measurement Rescue in 4,374 Virtual Subjects.*

## Scientific question

Can physiologically different age-conditioned cardiovascular states generate arterial pulse phenotypes that are experimentally indistinguishable, which physiological compensations create those aliases, and which complementary measurements resolve them?

The study uses the canonical Pulse Wave DataBase (PWDB) through VascuQuest. A VascuQuest virtual subject is a **simulation instance, not a patient or human participant**.

## Phase-governed execution

The repository is developed through manually reviewed phase pull requests:

0. Canonical trial specification
1. Computational engine qualification
2. Systematic evidence map
3. Prospective protocol/code lock
4. Full one-shot in-silico trial
5. Falsification and robustness
6. Scientific adjudication
7. Publication package

No phase is automatically merged. Biological cross-age aliasing outcomes are not permitted to be inspected before the Phase-3 lock.

## Current phase

**Phase 0 — Canonical trial specification**

The governing Phase-0 files are under [`protocol/`](protocol/):

- [`TRIAL_PROTOCOL_v1.0.md`](protocol/TRIAL_PROTOCOL_v1.0.md)
- [`estimands.yaml`](protocol/estimands.yaml)
- [`observation_arms.yaml`](protocol/observation_arms.yaml)
- [`uncertainty_model.yaml`](protocol/uncertainty_model.yaml)
- [`falsification_rules.yaml`](protocol/falsification_rules.yaml)
- [`PHASE_0_VALIDATION.md`](protocol/PHASE_0_VALIDATION.md)

## Data boundary

PWDB remains the external source of truth and is not re-hosted in this repository. Large source artifacts and future runtime checkpoints belong in persistent external storage and are referenced by checksums/provenance.

Canonical PWDB DOI: `10.5281/zenodo.3275625`  
VascuQuest: `https://github.com/KNOWDYN/VascuQuest`
