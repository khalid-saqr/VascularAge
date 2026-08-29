<div align="center">

# VascularAge

### Is Arterial Age Identifiable From the Pulse?

**An exhaustive in-silico trial of physiological aliasing and measurement rescue in 4,374 virtual haemodynamic simulations**

[![Trial](https://img.shields.io/badge/trial-COMPLETE-2ea44f?style=for-the-badge)](#trial-status)
[![Protocol](https://img.shields.io/badge/protocol-PROSPECTIVELY%20LOCKED-2563eb?style=for-the-badge)](phase3/LOCK_MANIFEST.json)
[![PWDB](https://img.shields.io/badge/PWDB-4%2C374%20simulations-6f42c1)](https://doi.org/10.5281/zenodo.3275625)
[![Pairs](https://img.shields.io/badge/cross--age%20pairs-7%2C971%2C615-8b5cf6)](#design)

</div>

---

## Trial status

The locked computational trial is **complete**. Qualification, evidence mapping, prospective protocol lock, confirmatory execution, robustness analysis, and the final tie-sensitivity closure have all been executed and audited.

| Stage | Status |
|---|---|
| Source / engine qualification | **PASS** |
| Evidence map and novelty collision audit | **PASS** |
| Prospective confirmatory protocol | **LOCKED** |
| Phase 4 confirmatory trial | **EXECUTED** |
| Amendment 001 | **EXECUTED** |
| Phase 5 S2 robustness | **PASS** |
| Phase 5B tie-sensitivity closure | **PASS** |
| Computational study | **COMPLETE** |

The authoritative scientific lock identities are:

```text
Phase 3 protocol lock
89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963

Phase 4 Amendment 001 lock
1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7

Phase 5 S2 lock
97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05

Phase 5B tie-sensitivity lock
6b9f11bf0c662c8263e531b0440882881d79b5ab70aaa4aaeffd4e4a69d741c2
```

---

## Scientific question

VascularAge tests whether arterial age is uniquely recoverable from arterial pulse phenotypes, rather than assuming that accurate age prediction implies physiological identifiability.

The inverse problem is:

```text
(age_1, physiology_1) != (age_2, physiology_2)
while
observation(age_1, physiology_1) ~= observation(age_2, physiology_2)
```

The study asks three linked questions:

1. Can different age-conditioned cardiovascular states generate experimentally indistinguishable pulses?
2. Which physiological compensations create those cross-age aliases?
3. Which additional vascular measurements remove ambiguity left by radial pressure alone?

---

## Design

The study uses the canonical Pulse Wave DataBase (PWDB), Zenodo record `3275625`, through the qualified VascuQuest data interface.

| Property | Value |
|---|---:|
| Virtual haemodynamic simulations | **4,374** |
| Model ages | **25, 35, 45, 55, 65, 75 years** |
| States per age | **729** |
| Factorial structure | **3^6** |
| Controlled factors | **HR, SV, LVET, DIA, PWV, MAP** |
| Unordered cross-age pairs | **7,971,615** |

A PWDB virtual subject is a simulation instance, not a patient. Reported alias proportions are therefore design prevalences over the complete factorial state space, not estimates of prevalence in a human population.

### Primary observation P0

P0 is absolute radial pressure in mmHg, periodically resampled to 512 phase points while retaining active-cycle duration.

For pair `(i,j)`:

```text
pressure discrepancy = RMSE(P_i, P_j)
duration discrepancy = |T_i - T_j|

d = sqrt((pressure_RMSE / eP)^2 + (duration_difference / eT)^2)
```

Reference tolerances are `eP = 5 mmHg` and `eT = 10 ms`; a pair is aliased when `d <= 1`.

Primary processing forbids mean subtraction, z-normalisation, peak scaling, pulse-pressure scaling, and subject-specific morphology normalisation.

---

## Main results

### Physiological aliasing

At the locked P0 reference tolerance:

| Result | Value |
|---|---:|
| Aliased cross-age pairs | **53,842** |
| Subjects participating in at least one alias | **2,764 / 4,374** |
| Subject alias fraction | **0.6319158665** |

Replication arms also contained substantial cross-age aliasing:

| Arm | Pair aliases | Alias-subject fraction |
|---|---:|---:|
| P0 Radial pressure | 53,842 | 0.6319 |
| P1 Digital PPG | 298,547 | 0.6591 |
| P2 Carotid pressure | 98,311 | 0.6507 |

### Measurement rescue

Measurement rescue was strictly nested from the P0 alias set.

| Arm | Surviving pair aliases | Surviving subjects | Rescue fraction |
|---|---:|---:|---:|
| M1 | 6,838 | 1,580 | 0.4284 |
| M2 | 0 | 0 | **1.0000** |
| M3 | 0 | 0 | **1.0000** |
| M4 | 0 | 0 | **1.0000** |

Within this factorial in-silico design, the richer M2 observation set eliminated every P0 reference alias, and the nested M3/M4 arms retained that complete rescue.

### Compensation motifs

For each P0-aliased source, the locked mechanism analysis used its canonical nearest cross-age target and the factor-change vector in order `(HR, SV, LVET, DIA, PWV, MAP)`.

| Quantity | Value |
|---|---:|
| Distinct motifs | **178** |
| Top-20 motif count | **1,609 / 2,764** |
| Top-20 concentration | **0.5821273517** |
| Locked null 95th percentile | **0.0336468886** |
| Locked permutations | **2,000** |
| S4 no-go | **false** |

### Phase 5 robustness

The prospectively locked S2 test replaced RMSE pressure discrepancy with matched-scale L1/MAE and Linf alternatives.

| Metric | Alias subjects | Jaccard vs P0 |
|---|---:|---:|
| P0 / RMSE | 2,764 | 1.0000 |
| L1 / MAE | 2,874 | **0.9617258177** |
| Linf / maximum error | 1,724 | **0.6237337192** |

The locked S2 no-go required **both** Jaccard values to be below `0.50`; it did not fire.

A post-execution mathematical audit notes that, under the identical scales and 512-point representation, `L1 <= L2(RMSE) <= Linf`. Consequently the L1 subject set contains P0 and, once the observed P0 prevalence was known, the L1 arm could not independently make the two-arm AND criterion fail. The Linf result remains independently informative and also exceeded the locked threshold. No retrospective threshold or adjudication was changed.

### Phase 5B tie-sensitivity closure

The Phase-3 protocol required the compensation analysis to be checked over co-nearest alternatives within `1e-6` of the minimum distance.

| Quantity | Result |
|---|---:|
| Subjects with co-nearest alternatives | **0 / 4,374** |
| P0-aliased sources with co-nearest alternatives | **0 / 2,764** |
| Maximum co-nearest count | **1** |
| Minimum nearest/second-nearest gap, all subjects | `1.4781951904296875e-05` |
| Minimum gap, P0 aliases | `4.976987838745117e-05` |
| Co-nearest-sensitive top-20 concentration | **0.5821273517** |
| Difference from canonical | **0.0** |
| Outcome | **NO_CO_NEAREST_ALTERNATIVES** |

Thus the canonical smallest-index tie-break never resolved an actual tie among subjects entering the compensation analysis.

---

## Falsification status

The trial was prospectively designed to permit failure or downgrade through rules S1-S7. None of the locked no-go or downgrade rules fired in the completed trial.

The formal adjudications and their implementation are preserved in the Phase-3, Phase-4, Phase-5, and Phase-5B packages. No result in this README changes those locked definitions.

---

## Repository structure

```text
VascularAge/
├── phase1/      qualification contract and audit
├── phase2/      evidence map, screening and novelty collision audit
├── phase3/      prospectively locked confirmatory protocol
├── phase4/      Amendment 001 and confirmatory execution contract
├── phase5/      S2 robustness lock and post-execution audit
├── phase5b/     final tie-sensitivity lock and audit
├── notebooks/   executed Colab notebooks retained as provenance
├── src/         scientific analysis primitives
├── scripts/     guarded execution and validation entry points
├── tests/       deterministic unit / known-answer tests
└── .github/     continuous validation
```

Development and execution artifacts are retained only where they contribute to protocol provenance, reproducibility, or auditability.

---

## Reproducibility and evidence

The large biological evidence bundles are not duplicated in Git. Their exact identities are bound through SHA-256 manifests and post-execution audit records.

Key preserved Phase-4 source hashes include:

```text
primary_pair_components.npz
f4e411dab367bf758466c89d65dcf261b2518af6fbd718b83eae9c2e021184bf

primary_subject_results.csv
aa20eb842496e8ad3bb85232bafff18ba4724903f76f1e79e6b1ff3da036829a
```

Phase 5B independently reverified the preserved Phase-4 artifacts before closing the final sensitivity obligation.

The executed notebooks are retained in `notebooks/` as immutable execution provenance; the scientific definitions live in the locked JSON/Markdown packages and Python analysis modules rather than in notebook outputs.

---

## Validation

Local validation:

```bash
python -m pip install -e ".[test]" "jax[cpu]"
pytest -q
python scripts/validate_phase1_static.py
python scripts/phase2_validate.py
python scripts/phase3_validate.py
python scripts/validate_phase4_amendment001.py
python scripts/validate_phase5_s2.py
python scripts/validate_phase5b.py
```

GitHub Actions performs the same repository-wide validation and verifies that guarded execution entry points cannot run their biological/evidence endpoints without the explicit locked execution flags.

---

## Data source

Pulse Wave DataBase (PWDB), Zenodo DOI: **10.5281/zenodo.3275625**.

The repository does not claim that the virtual-subject design establishes clinical diagnostic performance. It tests identifiability and measurement ambiguity inside the specified in-silico factorial system.
