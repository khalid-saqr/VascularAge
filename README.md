<div align="center">

# VascularAge

### Is Arterial Age Identifiable From the Pulse?

**An exhaustive in-silico trial of physiological aliasing and measurement rescue in 4,374 virtual haemodynamic simulations**

[![Protocol](https://img.shields.io/badge/protocol-PROSPECTIVELY%20LOCKED-2ea44f?style=for-the-badge)](phase3/LOCK_MANIFEST.json)
[![Phase 4](https://img.shields.io/badge/Phase%204-ON%20HOLD-f59e0b?style=for-the-badge)](#current-controlled-state)
[![Endpoints](https://img.shields.io/badge/biological%20endpoints-NOT%20EXECUTED-2563eb?style=for-the-badge)](#current-controlled-state)

[![PWDB](https://img.shields.io/badge/PWDB-4%2C374%20simulations-6f42c1)](https://doi.org/10.5281/zenodo.3275625)
[![Design](https://img.shields.io/badge/design-6%20ages%20%C3%97%20729%20states-0ea5e9)](#trial-population)
[![Cross-age pairs](https://img.shields.io/badge/cross--age%20pairs-7%2C971%2C615-8b5cf6)](#primary-confirmatory-analysis)
[![Compute](https://img.shields.io/badge/compute-JAX%20%2F%20XLA-111827)](#computational-contract)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.3275625-blue)](https://doi.org/10.5281/zenodo.3275625)

</div>

---

## Scientific objective

**VascularAge** implements **The Locked In-Silico Trial Concept**: a prospectively specified computational experiment testing whether arterial age is uniquely recoverable from the arterial pulse.

The trial asks three linked questions:

1. **Physiological aliasing:** can different age-conditioned cardiovascular states produce arterial pulse phenotypes that are experimentally indistinguishable?
2. **Mechanism:** which controlled physiological compensations create those cross-age aliases?
3. **Measurement rescue:** which additional vascular measurements eliminate ambiguity that remains when radial pressure is observed alone?

The central inverse-problem formulation is:

\[
(a_1,\theta_1) \neq (a_2,\theta_2)
\quad\text{while}\quad
Y(a_1,\theta_1) \approx Y(a_2,\theta_2).
\]

The project therefore does **not** assume that a pulse-derived age estimate is physiologically unique merely because a predictive model can estimate age accurately.

---

## Current controlled state

| Control | Status |
|---|---|
| Canonical trial specification | **Frozen** |
| PWDB / VascuQuest source qualification | **PASS** |
| JAX/XLA computational qualification | **PASS** |
| Systematic evidence map and collision audit | **PASS** |
| Prospective confirmatory protocol | **Cryptographically locked** |
| Real cross-age biological endpoints | **Not executed** |
| Phase 4 full trial | **ON HOLD — explicit execution command required** |

> **Execution control:** Phase 4 must remain unexecuted until an explicit project command authorizes it. The presence of the guarded Phase-4 runner in the repository is not permission to run the biological trial.

The merged Phase-3 lock package is identified by:

```text
89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963
```

The complete cryptographic basis is recorded in [`phase3/LOCK_MANIFEST.json`](phase3/LOCK_MANIFEST.json).

---

## Trial population

The trial uses the canonical **Pulse Wave DataBase (PWDB)**, Zenodo record **3275625**, accessed through the qualified VascuQuest interface.

| Property | Locked value |
|---|---:|
| Virtual haemodynamic simulation instances | **4,374** |
| Model ages | **25, 35, 45, 55, 65, 75 years** |
| States per age | **729** |
| Factorial structure | **3⁶** |
| Standardised factor levels | **−1, 0, +1** |
| Controlled factors | **HR, SV, LVET, DIA, PWV, MAP** |
| PWDB source mapping for MAP | **`MBP`** |

The locked factor order is:

```text
HR → SV → LVET → DIA → PWV → MAP
```

### Interpretation boundary

A PWDB `VirtualSubject` is a **simulation instance, not a patient**. The six age-conditioned state spaces are not longitudinal observations of the same biological individuals. Repeated standardised configurations across ages are therefore described as **configuration-matched cross-age simulations**.

Any reported alias proportion is a **design prevalence across the complete factorial state space**, not an estimate of prevalence in a human population.

---

## Primary confirmatory analysis

### P0 — Radial pressure

The primary observation is the source radial pressure waveform:

```text
site      = Radial
quantity  = pressure
unit      = mmHg
samples   = 512 phase points
```

Active source samples are identified using the qualified VascuQuest missing/padding semantics. Each cardiac cycle is mapped periodically to phase \(\phi\in[0,1)\) using periodic linear interpolation while preserving absolute pressure amplitude and the original cycle duration.

The primary analysis forbids subject-specific:

- mean subtraction;
- z-normalisation;
- peak scaling;
- pulse-pressure scaling;
- morphology normalisation.

### Pair universe

Every state is compared with every state belonging to a different age group. The locked universe contains:

\[
\binom{6}{2}\times729^2 = \mathbf{7,971,615}
\]

unordered cross-age pairs across all 15 age-pair combinations.

For pair \((i,j)\):

\[
\Delta P_{ij}=\sqrt{\operatorname{mean}\left[(P_i-P_j)^2\right]},
\]

\[
\Delta T_{ij}=|T_i-T_j|,
\]

and the reference separation is

\[
d_{ij}=\sqrt{\left(\frac{\Delta P_{ij}}{5\;\mathrm{mmHg}}\right)^2+
\left(\frac{\Delta T_{ij}}{10\;\mathrm{ms}}\right)^2}.
\]

A reference pair is classified as **aliased** when:

\[
d_{ij}\le1.
\]

The primary tolerance surface is fully prespecified:

- pressure RMS tolerance: **1, 2, 3, 5, 8, 10 mmHg**;
- cycle-duration tolerance: **2, 5, 10, 20 ms**;
- total locked grid: **24 tolerance points**.

The primary subject-level estimand is the minimum cross-age separation

\[
D_i=\min_{j:\,a_j\neq a_i}d(i,j),
\]

with a deterministic tie rule: candidates within `1e-6` of the minimum use the smallest global target-row index.

---

## Replication and measurement rescue

The confirmatory design distinguishes **replication** from **measurement rescue**.

### Replication arms

| Arm | Observation | Role |
|---|---|---|
| **P1** | Digital PPG | Shape-only replication using centred unit-RMS morphology plus duration |
| **P2** | Carotid pressure | Pressure replication using the P0 operator |

Digital PPG is handled as an arbitrary-unit morphology signal; it is not given an artificial physical amplitude scale.

### Strictly nested rescue hierarchy

Measurement rescue is evaluated only among pairs that remain aliases under the P0 reference definition.

```mermaid
graph LR
    P0["P0 · Radial pressure"] --> M1["M1 · + Carotid area"]
    M1 --> M2["M2 · + Carotid pressure + reconstructed flow"]
    M2 --> M3["M3 · + AorticRoot / Radial / Femoral mechanics"]
    M3 --> M4["M4 · All 13 common sites · P / Q / A"]
```

A source state is **rescued** when it has at least one P0 reference alias but no surviving alias under the richer observation arm.

For area and reconstructed flow, the locked comparison operator is symmetric relative RMS:

\[
r(x,y)=\frac{\operatorname{RMS}(x-y)}
{\sqrt{\tfrac12\left(\operatorname{RMS}(x)^2+\operatorname{RMS}(y)^2\right)}}.
\]

The reference relative tolerance is **5%**, with a locked grid of **1%, 2%, 5%, 10%, 20%**.

Reconstructed flow is calculated as \(Q=U\,A\) and retains VascuQuest evidence status **RECONSTRUCTED**.

### M4 common-site upper bound

The complete mechanical upper-bound arm uses pressure, reconstructed flow and luminal area across the 13 qualified common sites:

`AorticRoot`, `ThorAorta`, `AbdAorta`, `IliacBif`, `Carotid`, `SupTemporal`, `SupMidCerebral`, `Brachial`, `Radial`, `Digital`, `CommonIliac`, `Femoral`, and `AntTibial`.

---

## Physiological compensation analysis

For a source state and its canonical nearest cross-age target, compensation is represented in the locked standardised factor coordinates as

\[
\Delta\xi=\xi_{\text{target}}-\xi_{\text{source}}.
\]

The analysis retains the exact six-dimensional vector in the locked factor order and evaluates recurring motifs among P0 reference-aliased states.

The confirmatory mechanism test uses:

- top **20** compensation motifs;
- **2,000** locked null permutations;
- random seed **20260829**;
- null target age preserved while target state is sampled uniformly from the 729 states at that age.

The mechanism claim fails its prespecified S4 criterion if the observed top-20 motif concentration does not exceed the 95th percentile of the locked null distribution.

---

## Conventional vascular-age benchmark

The full-waveform result is benchmarked against source-supported conventional quantities:

- aortic pulse-wave velocity;
- aortic augmentation index;
- brachial systolic pressure.

A prespecified novelty downgrade is triggered if aortic PWV alone reproduces the P0 alias structure with both:

- pair-alias Jaccard **≥ 0.90**; and
- subject-level alias-existence agreement **≥ 0.95**.

These comparisons prevent a full-waveform result from being presented as novel if the same structure is already captured by a conventional scalar vascular-age metric.

---

## Local information geometry

Local observability is a secondary explanatory analysis, not the novelty headline.

At the baseline factorial state \(\xi=(0,0,0,0,0,0)\) for each age, the locked analysis constructs a Jacobian with respect to the six standardised factors using central \(\pm1\) perturbations and evaluates

\[
F=J^\top J.
\]

Reported quantities include:

- eigenvalues and eigenvectors;
- condition number;
- weakest observable direction;
- age evolution of local information geometry.

A Fisher-information interpretation is made only under the corresponding isotropic Gaussian measurement model; otherwise \(F\) is treated as a local pullback/information metric.

---

## Falsification and downgrade rules

The trial is designed to be able to fail.

| Rule | Consequence |
|---|---|
| **S1** | No-go for major aliasing if alias fraction is <1% at every P0 tolerance point |
| **S2** | No-go for robust aliasing if legitimate alternative pressure metrics produce poor alias-set agreement in Phase 5 |
| **S3** | No-go for physiological aliasing if the result is predominantly a heart-period artefact |
| **S4** | No-go for compensation mechanism if motif concentration does not exceed the locked null |
| **S5** | Novelty downgrade if PWV alone essentially reproduces the full-waveform alias structure |
| **S6** | No-go for measurement rescue if every M1–M4 rescue fraction is <10% |
| **S7** | Primary claim invalid if forbidden subject-specific normalisation becomes necessary |

The exact machine-readable definitions are authoritative in [`phase3/LOCKED_TRIAL_CONFIG.json`](phase3/LOCKED_TRIAL_CONFIG.json).

---

## Computational contract

The confirmatory engine is designed for JAX/XLA execution on Google Colab-class hardware while remaining numerically auditable.

| Item | Locked choice |
|---|---|
| Production arithmetic | **float32** |
| CPU reference arithmetic | **float64** |
| JAX x64 production mode | **disabled** |
| Age-pair block | **729 × 729** |
| Pair index dtype | **int32** |
| Pair component storage | **float32** |
| Numerical audit | deterministic 60-state sample + every state near the alias boundary |
| Audit STOP condition | `D_ref` disagreement > `1e-4` or changed alias classification |

Phase 1 independently qualified the source boundary and synthetic JAX engine on Google Colab T4 before the confirmatory protocol was locked. Its external qualification recorded:

```text
status                       PASS
biological_endpoint_executed false
VascuQuest commit            79891036e61df3096536da8f647f2297b0d88252
Phase-1 contract SHA-256     18cc85b8e192b14acdfff7f08bd684704799e793b34bb558cfede0efbc5f0399
```

---

## Data and evidence semantics

VascuQuest is the qualified interface to canonical PWDB record `3275625`. The trial uses the following evidence classes consistently:

| Quantity | Evidence |
|---|---|
| Pressure | **SOURCE** |
| Flow velocity | **SOURCE** |
| Luminal area | **SOURCE** |
| Digital PPG | **SOURCE** |
| Reconstructed flow \(Q=UA\) | **RECONSTRUCTED** |

The trial does not rehost PWDB and does not reinterpret virtual simulations as observed human participants.

---

## Evidence and novelty boundary

The novelty boundary was fixed before biological execution using a frozen **889-record Scopus evidence map**, a **111-record high-relevance collision audit**, **50 seeded negative controls**, and a targeted current collision audit.

The permitted claim is deliberately narrow:

> Within the mapped evidence and targeted collision audit, no study was identified that explicitly treats arterial age as a global non-unique inverse problem by exhaustively testing whether distinct age-conditioned cardiovascular states can generate observationally indistinguishable arterial pulse phenotypes, mapping the physiological compensations that create those aliases, and quantifying which additional vascular measurements resolve them.

The project does **not** claim to be the first cardiovascular identifiability study, pulse-wave inverse problem, cardiovascular sloppiness study, multimodal identifiability study, vascular-age estimator, or arterial system-identification study.

See [`phase3/NOVELTY_BOUNDARY.md`](phase3/NOVELTY_BOUNDARY.md) and [`phase2/`](phase2/) for the evidence package and limitations.

---

## Reproducibility and protocol integrity

The Phase-3 lock cryptographically binds:

- the canonical Phase-0 protocol and estimands;
- the externally executed Phase-1 qualification contract and notebook;
- the Phase-2 evidence/novelty boundary;
- the exact confirmatory configuration;
- the mathematical analysis primitives;
- qualified PWDB preparation semantics;
- the guarded Phase-4 runner;
- the required Phase-4 output inventory.

The authoritative lock identifier is:

```text
89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963
```

The guarded runner [`scripts/phase4_execute_locked.py`](scripts/phase4_execute_locked.py) requires both the explicit `--execute-locked-trial` flag and the matching protocol lock. **While Phase 4 is on hold, that runner must not be invoked against the real PWDB trial.**

---

## Repository map

| Path | Authority |
|---|---|
| [`README.md`](README.md) | Authoritative project overview and current controlled state |
| [`protocol/`](protocol/) | Canonical scientific specification, estimands, observation arms, uncertainty and falsification rules |
| [`notebooks/01_engine_qualification.ipynb`](notebooks/01_engine_qualification.ipynb) | Executed external Phase-1 qualification evidence |
| [`phase1/`](phase1/) | Source/engine qualification contract and audit documentation |
| [`phase2/`](phase2/) | Systematic evidence map, collision audit, novelty statement and review limitations |
| [`phase3/LOCKED_TRIAL_CONFIG.json`](phase3/LOCKED_TRIAL_CONFIG.json) | Machine-readable confirmatory trial specification |
| [`phase3/ANALYSIS_PLAN.md`](phase3/ANALYSIS_PLAN.md) | Human-readable confirmatory analysis plan |
| [`phase3/LOCK_MANIFEST.json`](phase3/LOCK_MANIFEST.json) | Cryptographic protocol lock and provenance |
| [`phase3/LOCKED_OUTPUT_SCHEMA.json`](phase3/LOCKED_OUTPUT_SCHEMA.json) | Required full-trial output inventory |
| [`src/vascularage/confirmatory.py`](src/vascularage/confirmatory.py) | Locked mathematical analysis primitives |
| [`src/vascularage/locked_io.py`](src/vascularage/locked_io.py) | Locked qualified PWDB preparation semantics |
| [`scripts/phase4_execute_locked.py`](scripts/phase4_execute_locked.py) | Guarded full-trial runner — currently on hold |
| [`tests/`](tests/) | Qualification and protocol-lock regression tests |

---

## Required Phase-4 output contract

When Phase 4 is eventually authorized, the locked runner must produce the following inventory without modifying scientific parameters:

```text
execution_provenance.json
primary_subject_results.csv
primary_tolerance_surface.csv
primary_age_pair_matrix.csv
primary_pair_components.npz
replication_summary.csv
compensation_vectors.csv
compensation_motifs.csv
compensation_null_summary.json
measurement_rescue_summary.csv
conventional_benchmark.json
information_geometry.json
numerical_audit.json
trial_summary.json
```

Until explicit authorization is issued, these biological trial outputs must not be generated from real PWDB cross-age comparisons.

---

## Source references

**Pulse Wave DataBase (PWDB)**  
Charlton PH *et al.* *Modeling arterial pulse waves in healthy aging: a database for in silico evaluation of hemodynamics and pulse wave indexes.* American Journal of Physiology–Heart and Circulatory Physiology, 2019. DOI: [`10.1152/ajpheart.00218.2019`](https://doi.org/10.1152/ajpheart.00218.2019)

Canonical dataset: [`10.5281/zenodo.3275625`](https://doi.org/10.5281/zenodo.3275625)

**VascuQuest**  
The trial accesses PWDB through the qualified VascuQuest source/API semantics pinned at commit:

```text
79891036e61df3096536da8f647f2297b0d88252
```

---

<div align="center">

### Protocol locked. Biological outcome unseen. Phase 4 on hold.

</div>
