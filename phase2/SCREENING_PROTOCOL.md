# Phase 2 screening protocol — frozen-corpus evidence map and collision audit

## Objective

Establish the defensible literature boundary for **The Locked In-Silico Trial Concept** without executing any VascuQuest biological endpoint.

The review question is:

> How has arterial pulse-wave information been used to characterize vascular ageing, and to what extent has existing work explicitly addressed global non-uniqueness of age-conditioned pulse phenotypes, the cardiovascular compensations that create such aliases, and the measurements required to resolve them?

## Design

Phase 2 is an **evidence map plus structured collision audit**, not a meta-analysis. The 889-record Scopus export is heterogeneous and does not supply a common quantitative estimand suitable for statistical pooling.

### Layer A — frozen-corpus map

The retained 889-record export is identified by SHA-256 in `CORPUS_MANIFEST.json`. Only raw bibliographic fields and title/abstract text are used for the new coding. All previously generated Mori–Zwanzig-oriented labels are ignored.

Transparent regular-expression axes in `ontology.json` map the full corpus. These axes are descriptive retrieval aids, not evidence of absence.

### Layer B — high-relevance adjudication

Exactly **111** records are adjudicated at title/abstract level. The candidate set is the union of:

1. every record coded as vascular-age assessment;
2. every record jointly coded for ageing context and arterial pulse wave;
3. all 27 records previously flagged as high methodological/mechanistic threats, used only as a recall safeguard.

Each is assigned C0–C3 using the collision definitions in `ontology.json`.

### Layer C — negative-control audit

A seeded random sample of **50** records from outside the high-relevance set is adjudicated (`seed=20260829`). This checks whether the deterministic candidate rule is obviously omitting direct conceptual collisions.

### Layer D — targeted current collision audit

Because the exact original Scopus query is unavailable and the frozen corpus was partly oriented toward the earlier Mori–Zwanzig question, a separate current web/source search explicitly targets:
- cardiovascular identifiability/sloppiness;
- pulse-wave inverse problems;
- measurement-set dependence;
- vascular-age pulse analysis;
- physiological ambiguity/non-uniqueness.

The exact queries are retained in `TARGETED_SEARCH_LOG.md`. Strong neighbours are source-checked and recorded in `external_collision_audit.csv`.

## Collision definitions

- **C0 direct collision** — executes the locked conjunction: age-conditioned arterial pulse non-uniqueness/aliasing from known generating states, mechanistic compensation mapping, and/or measurement rescue.
- **C1 strong conceptual threat** — direct cardiovascular identifiability, inverse-problem, experimental-design or arterial-network inference precedent.
- **C2 strong domain neighbor** — vascular-age/pulse-wave or age-dependent arterial dynamics without the locked global aliasing/rescue conjunction.
- **C3 close neighbor** — related arterial-wave, reflection, transfer, ageing or system-identification work.

## Claim discipline

The evidence map may support only statements of the form **“no study was identified…”**. It must not support “no study exists” or “first cardiovascular identifiability study.”

## Reviewer structure and limitation

This phase is a single-reviewer/single-agent structured evidence map. Duplicate independent human screening was not performed and must not be implied. The collision subset and negative-control records are committed so another reviewer can reproduce or challenge the adjudications.

## Search reproducibility limitation

The exact Scopus query string that generated the 889-record export was not preserved. Therefore:
- the **corpus itself is reproducible by cryptographic hash**;
- the original **database retrieval is not exactly reproducible**;
- no exact query is fabricated retrospectively.

This limitation is explicit and materially narrows the role of Phase 2: it is a prospective novelty-boundary audit for the trial, not a claim of a fully reproducible standalone systematic review.

## Biological leakage boundary

Phase 2 must not compute any real-PWDB cross-age distance, nearest alias, alias prevalence, age-identifiability curve, compensation vector, or measurement-rescue result.
