# The Locked In-Silico Trial Concept — Phase 0 Trial Specification v1.0

**Project:** VascularAge  
**Working title:** *Is Arterial Age Identifiable From the Pulse? An Exhaustive In-Silico Trial of Physiological Aliasing and Measurement Rescue in 4,374 Virtual Subjects*  
**Phase:** 0 — Canonical trial specification  
**Status:** Frozen candidate specification for Phase-0 PR review  
**Data source:** Pulse Wave DataBase (PWDB), Zenodo record 3275625, DOI 10.5281/zenodo.3275625  
**Scientific interface:** VascuQuest 0.1.0 or later compatible release  
**Repository:** `khalid-saqr/VascularAge`

---

## 1. Purpose of Phase 0

Phase 0 defines the scientific question, experimental population, primary estimands, observation hierarchy, uncertainty framework, controls, falsification rules, and downstream execution constraints **before any substantive cross-age aliasing result is calculated**.

Phase 0 does **not**:
- calculate the primary biological endpoint;
- inspect cross-age nearest-neighbour results;
- optimise a metric against age separation;
- train an age-prediction model;
- declare a biological finding;
- alter PWDB or VascuQuest.

The Phase-0 specification is Layer A of the trial. Technical implementation details that cannot be resolved without validating source schemas or software behaviour are explicitly marked as Layer B and may be fixed in Phase 1, but must be frozen no later than Phase 3 and must not be chosen using substantive trial outcomes.

---

## 2. Scientific premise

Arterial pulse-wave ageing research commonly asks how pulse morphology, pulse-wave velocity, wave reflection, central pressure, pulse transit, stiffness, or derived vascular-age estimates change with age.

This trial asks the inverse question:

> **Can physiologically different age-conditioned cardiovascular states generate arterial pulse phenotypes that are experimentally indistinguishable, and if so, which physiological compensations create those aliases and which complementary measurements resolve them?**

The trial therefore tests the **identifiability of arterial age from the pulse under controlled physiological heterogeneity**, rather than constructing another vascular-age predictor.

---

## 3. Terminology and interpretation constraints

### 3.1 Virtual subjects

A PWDB/VascuQuest `VirtualSubject` is a simulation instance, not a human participant or patient.

The terms `virtual subject`, `simulation`, and `virtual haemodynamic state` may be used. The following interpretations are prohibited unless independently justified:
- patient;
- clinical participant;
- observed human subject;
- longitudinal observation of one biological individual;
- prevalence-weighted population sample.

### 3.2 Age

Age is a PWDB model attribute. Cross-age comparisons are **age-conditioned simulation contrasts**, not longitudinal ageing of an individual.

### 3.3 Physiological aliasing

A **cross-age physiological alias** is a virtual state at a different model age whose prespecified observable pulse representation lies within a prespecified measurement-tolerance region of an index state.

The concept is measurement-dependent. No pair may be called intrinsically identical without specifying the observation arm and tolerance model.

### 3.4 Measurement rescue

**Measurement rescue** occurs when an alias present under a poorer observation arm becomes distinguishable after adding a prespecified complementary observable and/or vascular site.

---

## 4. Canonical virtual population

The intended PWDB design is:

\[
6 \text{ ages} \times 3^6 \text{ physiological configurations}
= 6 \times 729
= 4,374 \text{ virtual simulations}.
\]

Target model ages:

\[
A \in \{25,35,45,55,65,75\}\text{ years}.
\]

The intended six controlled physiological/model coordinates are:

\[
\theta=(HR,SV,LVET,DIA,PWV,MAP),
\]

each represented at three age-specific standardized perturbation levels:

\[
\xi_k\in\{-1,0,+1\}.
\]

The complete standardized configuration is:

\[
\xi=(\xi_{HR},\xi_{SV},\xi_{LVET},\xi_{DIA},\xi_{PWV},\xi_{MAP}).
\]

### 4.1 Mandatory Phase-1 verification gate

Before any biological trial calculation, Phase 1 must verify from the canonical source representation that:
1. exactly 4,374 simulation identities are aligned across required source artifacts;
2. exactly six age groups exist and each contains 729 simulations;
3. the six factorial coordinates are exactly the intended quantities above, or an explicit protocol amendment is required;
4. each age contains all \(3^6\) standardized configurations exactly once;
5. subject identity and waveform identity are one-to-one and aligned;
6. Radial pressure is available for all intended subjects;
7. source time coordinates permit one complete cardiac-cycle representation per subject;
8. no source field is silently imputed.

Failure of any item stops progression to the trial until resolved by a documented protocol amendment.

---

## 5. Source-data boundary

The trial is designed to use only capabilities that VascuQuest declares available or explicitly reconstructed with provenance.

Expected Phase-0 source requirements:
- `pwdb_model_configs.csv`;
- factorial variation/configuration information sufficient to recover the six controlled coordinates;
- `pwdb_haemod_params.csv`;
- `pwdb_pw_indices.csv`;
- `pwdb_onset_times.csv`;
- `PWs_csv.zip`;
- optional `geo.zip` only for prespecified secondary interpretation, not the primary endpoint.

Primary source-supported waveforms:
- pressure \(P(t)\);
- flow velocity \(U(t)\);
- luminal cross-sectional area \(A(t)\);
- photoplethysmogram \(PPG(t)\).

Volumetric flow rate may be used only through the VascuQuest validated reconstruction:

\[
Q(t)=U(t)A(t),
\]

and must retain `RECONSTRUCTED` evidence status.

Dense path-resolved PWDB files are outside the primary trial.

---

## 6. Trial architecture

The trial has five nested scientific layers.

### Layer 1 — Global cross-age physiological aliasing

Determine whether a pulse produced by one age-conditioned physiological state can be observationally matched by a different physiological state at another age.

### Layer 2 — Matched-configurational ageing displacement

For the same standardized factorial coordinate \(\xi\), measure the pulse displacement across age. This provides the controlled reference displacement attributable to changing the age-conditioned arterial model while retaining the same standardized perturbation coordinates.

### Layer 3 — Physiological compensation

For each cross-age nearest alias, calculate the change in generating coordinates required to compensate for the age-conditioned pulse displacement.

### Layer 4 — Measurement rescue

Determine which additional prespecified measurements break aliases found under the primary observation.

### Layer 5 — Local information geometry

Use the factorial perturbations to estimate local Jacobian/Fisher structure as an explanatory analysis of globally observed aliases. This is not the primary discovery endpoint.

---

## 7. Primary observation arm

The primary observation is:

\[
\boxed{P_{\mathrm{radial}}(t)}
\]

from the canonical `Radial` measurement site.

### 7.1 Primary waveform representation

For every source waveform:
1. retain the source cycle duration \(T\);
2. map the single cardiac cycle monotonically to phase \(\phi\in[0,1)\);
3. linearly interpolate pressure to exactly 512 uniformly spaced phase samples;
4. retain absolute pressure amplitude in physical units, converted to mmHg for reporting;
5. perform **no subject-specific mean subtraction, z-normalisation, peak scaling, pulse-pressure scaling, or morphology normalisation** in the primary analysis.

The resulting primary observation is:

\[
Y_i=(P_i(\phi_1),\ldots,P_i(\phi_{512}),T_i).
\]

Cycle duration remains an observable; phase resampling does not erase heart-rate information.

### 7.2 Primary pairwise components

For two virtual states \(i,j\):

\[
\Delta P_{ij}
=
\sqrt{\frac{1}{512}
\sum_{m=1}^{512}
[P_i(\phi_m)-P_j(\phi_m)]^2}
\quad \text{mmHg},
\]

and

\[
\Delta T_{ij}=|T_i-T_j|
\quad \text{ms}.
\]

These two quantities remain separately reportable.

### 7.3 Reference separation index

For operational reference only, define:

\[
d_{ij}^{ref}
=
\sqrt{
\left(\frac{\Delta P_{ij}}{5\ {\rm mmHg}}\right)^2
+
\left(\frac{\Delta T_{ij}}{10\ {\rm ms}}\right)^2
}.
\]

A reference alias has:

\[
d_{ij}^{ref}\le1.
\]

The 5-mmHg pressure scale is a measurement-tolerance reference, not a claim that radial tonometry has a universal 5-mmHg error. It is anchored to the order of magnitude used in the AAMI/ESH/ISO universal blood-pressure device validation criterion and is deliberately stress-tested over a wider grid. The 10-ms period scale is an operational timing tolerance, likewise subjected to sensitivity analysis.

The full tolerance surface, not the single reference threshold, is the principal robustness representation.

---

## 8. Primary estimands

### 8.1 Nearest cross-age separation

For each state \(i\):

\[
D_i^{ref}
=
\min_{j:A_j\ne A_i}
d_{ij}^{ref}.
\]

The minimizing state is:

\[
j_i^\star
=
\arg\min_{j:A_j\ne A_i} d_{ij}^{ref}.
\]

### 8.2 Primary alias prevalence in the factorial design

Define:

\[
\Pi_{alias}^{ref}
=
\frac{1}{4374}
\sum_i
\mathbf 1[D_i^{ref}\le1].
\]

This is a **design prevalence across equally weighted factorial simulation states**, not a prevalence estimate for humans.

### 8.3 Age-identifiability surface

For tolerance pair \((\epsilon_P,\epsilon_T)\), define:

\[
d_{ij}(\epsilon_P,\epsilon_T)
=
\sqrt{
\left(\frac{\Delta P_{ij}}{\epsilon_P}\right)^2
+
\left(\frac{\Delta T_{ij}}{\epsilon_T}\right)^2
},
\]

and

\[
R(\epsilon_P,\epsilon_T)
=
\frac{1}{4374}
\sum_i
\mathbf 1[
\min_{j:A_j\ne A_i}d_{ij}(\epsilon_P,\epsilon_T)>1
].
\]

\(R\) is the fraction of factorial design states that remain cross-age distinguishable at the stated tolerances.

### 8.4 Age-pair matrix

For all 15 unordered age pairs \((a,b)\), compute pair-specific nearest separation and alias fractions. The all-age primary analysis is confirmatory; the 25-vs-75 extreme-age contrast is a prespecified secondary contrast.

---

## 9. Controlled matched-age displacement

For standardized configuration \(\xi\) and two ages \(a,b\), define the matched pair:

\[
Y(a,\xi),Y(b,\xi).
\]

Its reference separation is:

\[
D_{matched}(a,b,\xi)
=
d^{ref}[Y(a,\xi),Y(b,\xi)].
\]

For the same source state \(Y(a,\xi)\), define the best target-age state:

\[
D_{best}(a\rightarrow b,\xi)
=
\min_{\eta\in\{-1,0,+1\}^6}
d^{ref}[Y(a,\xi),Y(b,\eta)].
\]

Define physiological compensation gain:

\[
G_{comp}
=
1-
\frac{D_{best}}{D_{matched}+\delta},
\]

where \(\delta\) is a fixed numerical guard used only to avoid division by zero and must be \(<10^{-12}\) in double precision.

Interpretation:
- \(G_{comp}\approx0\): physiological variation at the target age provides little improvement over the matched standardized configuration;
- \(G_{comp}\rightarrow1\): another target-age physiological state nearly erases the matched age-associated pulse displacement.

The untransformed \(D_{best}\) and \(D_{matched}\) remain the authoritative quantities; \(G_{comp}\) is a summary.

---

## 10. Physiological compensation vectors

For each directed source-age to target-age nearest alias:

\[
\Delta\xi
=
\xi_{target}^\star-\xi_{source}.
\]

Both of the following must be retained:
1. exact discrete compensation vector in standardized \(-1/0/+1\) coordinates;
2. physical parameter changes when canonical source values are available.

Analyses may summarize:
- exact-vector frequency;
- sign-pattern frequency;
- marginal change frequency by factor;
- age-pair-specific compensation patterns;
- cardiac versus vascular components.

No compensation vector may be interpreted causally outside the controlled simulation design.

---

## 11. Prespecified observation/rescue hierarchy

Observation arms are ordered. Each richer arm must be compared with its immediate predecessor and with the primary arm.

1. **P0 — Radial pressure**: primary arm.
2. **P1 — Digital PPG**: wearable/optical replication, morphology-only semantics appropriate to the source.
3. **P2 — Carotid pressure**: central-arterial replication.
4. **M1 — Radial pressure + carotid area**.
5. **M2 — Carotid pressure + carotid reconstructed flow + carotid area**.
6. **M3 — Prespecified multi-site mechanical observation**, using pressure/flow/area at a restricted set of anatomically distributed sites fixed in Phase 3.
7. **M4 — Complete available common-site mechanical observation**, theoretical information upper bound.

Cross-unit multimodal arms must **not** be formed by arbitrary concatenation with ad-hoc weights. A pair remains aliased under multimodal observation only when it satisfies each modality's independently prespecified tolerance criterion (logical intersection), unless Phase 1 validates an alternative likelihood model before results are inspected.

Detailed modality-specific normalisation/tolerance operators for PPG, area, and flow are Layer-B implementation choices and must be justified by source units and measurement semantics, validated in Phase 1, and frozen in Phase 3.

---

## 12. Prespecified tolerance/uncertainty domain

The primary radial-pressure tolerance surface must include at minimum:

Pressure RMS tolerance, mmHg:

\[
\epsilon_P\in\{1,2,3,5,8,10\}.
\]

Cycle-duration tolerance, ms:

\[
\epsilon_T\in\{2,5,10,20\}.
\]

Reference operating point:

\[
(\epsilon_P,\epsilon_T)=(5\ {\rm mmHg},10\ {\rm ms}).
\]

The grid is a controlled computational stress domain, not an epidemiological distribution of device errors.

Phase 5 must additionally test:
- additive waveform noise;
- multiplicative gain/calibration error;
- pressure offset error;
- temporal jitter;
- reduced sampling frequency;
- alternative legitimate waveform distance definitions.

Stochastic perturbations belong to the measurement process only. The 729 factorial configurations per age are not assigned empirical human prevalence probabilities.

---

## 13. Conventional status-quo comparators

The trial must compare full-waveform age identifiability with source-supported conventional scalar representations available through VascuQuest/PWDB, including where semantically and technically validated:

- aortic pulse-wave velocity;
- pulse pressure;
- aortic augmentation index / source-supported augmentation measure;
- source onset/transit timing quantities;
- selected simple pulse morphology descriptors defined before Phase 4.

The exact canonical field names and units are resolved in Phase 1. No comparator may be silently substituted if unavailable.

Purpose:
1. determine whether conventional indices discard age-discriminating information present in the waveform;
2. determine whether the full waveform is itself physiologically non-unique;
3. determine whether multimodal measurement resolves ambiguity that feature engineering cannot.

---

## 14. Local information-geometry analysis

This analysis is explanatory, not primary.

At eligible central factorial states, estimate the local observation Jacobian with respect to:

\[
(HR,SV,LVET,DIA,PWV,MAP).
\]

A local Fisher-type metric may be constructed only after the observation-noise covariance is explicitly defined and validated:

\[
F=J^\top\Sigma^{-1}J.
\]

Report:
- eigenvalues;
- condition number;
- least-observable eigenvectors;
- age evolution of local sloppy/stiff directions.

The purpose is to explain global aliasing, not to rename sensitivity analysis as the primary discovery.

---

## 15. Primary hypotheses

### H1 — Cross-age physiological aliasing

Under the prespecified primary radial-pressure observation, at least some distinct age-conditioned physiological states will satisfy the reference alias criterion and form a non-trivial cross-age alias structure.

This is tested by \(\Pi_{alias}^{ref}\), the distribution of \(D_i^{ref}\), and the full \(R(\epsilon_P,\epsilon_T)\) surface.

### H2 — Structured physiological compensation

Nearest cross-age aliases will exhibit reproducible non-random patterns in the six controlled generating coordinates rather than uniformly distributed arbitrary compensation vectors.

### H3 — Measurement rescue

At least one prespecified complementary observation arm will reduce cross-age aliasing relative to radial pressure alone under matched tolerance semantics.

No directional hypothesis is prespecified for which physiological factor dominates or which rescue arm is optimal.

---

## 16. Descriptive rather than epidemiological inference

The entire factorial design is exhaustively enumerated. Primary summaries are therefore deterministic properties of the virtual design.

The trial must not manufacture conventional population significance by treating 4,374 simulations as an i.i.d. sample of humans.

Allowed inferential tools include:
- exact factorial contrasts;
- exhaustive counts/proportions of design states;
- permutation tests when testing structure against a clearly defined null assignment;
- bootstrap or Monte Carlo uncertainty only for measurement/noise processes or estimator stability;
- sensitivity analyses across prespecified uncertainty domains.

Human prevalence or clinical-risk claims require external human validation and are outside this trial.

---

## 17. Leakage and outcome-shopping controls

Before Phase 3 lock:
- Phase 1 may access data only for source qualification, schema validation, waveform semantics, and known-answer software tests.
- Phase 2 may use the 889-record evidence corpus to refine the defensible novelty statement.
- No cross-age nearest-neighbour table, alias prevalence, age-pair heatmap, or rescue result may be inspected.

After Phase 3 lock:
- Phase 4 executes the primary trial from machine-readable configuration.
- No distance metric, tolerance, observation ordering, exclusion rule, or primary endpoint may be altered in response to Phase-4 results.
- Any deviation must be recorded in an amendment log and labelled exploratory.

---

## 18. Phase-0 hard-stop conditions

Phase 0 itself fails if:
1. the protocol contains contradictory definitions across human-readable and machine-readable files;
2. the primary observation cannot be represented without hidden normalization choices;
3. the primary endpoint depends on an undefined probability distribution over virtual subjects;
4. the protocol describes virtual subjects as human participants;
5. a downstream implementation decision is allowed to depend on biological results.

---

## 19. Downstream scientific falsification rules

The major concept is weakened or falsified according to the rules in `falsification_rules.yaml`.

At minimum, the major claim cannot survive if:
- cross-age aliasing is negligible across the prespecified realistic/stress tolerance domain;
- alias structure disappears under reasonable legitimate waveform-distance alternatives;
- the effect is a trivial consequence of heart-rate/cycle-duration differences;
- physiological compensation vectors show no reproducible structure;
- conventional single metrics fully explain the phenomenon;
- measurement rescue is absent or unstable;
- results depend on subject-specific normalization forbidden by the primary protocol.

---

## 20. Reproducibility and provenance

Every Phase-4 result must eventually record:
- PWDB record/DOI;
- VascuQuest version and Git commit;
- canonical artifact checksums;
- subject IDs;
- age/configuration coordinates;
- observation arm;
- source/reconstructed evidence classes;
- resampling specification;
- tolerance specification;
- code commit;
- JAX/Python package versions;
- numerical precision;
- random seed for stochastic robustness analyses.

Large PWDB artifacts and runtime checkpoints are not committed to this repository. They will reside in persistent Google Drive storage with checksums and manifests.

---

## 21. Trial execution boundary

The Locked In-Silico Trial Concept proceeds only through manually reviewed phase PRs:

- Phase 0 — trial specification;
- Phase 1 — computational engine qualification;
- Phase 2 — systematic evidence map;
- Phase 3 — prospective protocol/code lock;
- Phase 4 — full one-shot in-silico trial;
- Phase 5 — falsification and robustness;
- Phase 6 — scientific adjudication;
- Phase 7 — publication package.

No phase may be merged automatically.

---

## 22. External measurement-reference note

The 5-mmHg reference pressure tolerance is used as an operational mid-grid scale and is not asserted to be a validated radial-tonometry accuracy specification.

AAMI/ESH/ISO universal BP-device validation literature uses a 5-mmHg mean-error criterion with an 8-mmHg standard-deviation criterion for conventional BP device validation. The trial therefore uses 5 mmHg only as a recognizable reference order of magnitude while reporting the complete 1–10 mmHg stress grid.

Reference:  
Stergiou GS, et al. *A Universal Standard for the Validation of Blood Pressure Measuring Devices: AAMI/ESH/ISO Collaboration Statement.* Hypertension. 2018;71:368–374. doi:10.1161/HYPERTENSIONAHA.117.10237.

---

## 23. Phase-0 acceptance criteria

Phase 0 is cleared only if:
- [ ] scientific premise is singular and testable;
- [ ] virtual-subject semantics are explicit;
- [ ] intended factorial design and mandatory verification gate are explicit;
- [ ] primary observation is frozen;
- [ ] primary waveform representation is frozen;
- [ ] primary pairwise separation is dimensionally defined;
- [ ] primary estimands are mathematically defined;
- [ ] the uncertainty domain is prespecified;
- [ ] rescue hierarchy is prespecified;
- [ ] conventional comparator purpose is prespecified;
- [ ] local Fisher analysis is secondary/explanatory;
- [ ] no epidemiological weighting of factorial states is introduced;
- [ ] leakage controls are explicit;
- [ ] falsification rules are machine-readable;
- [ ] no substantive biological result has been calculated in Phase 0.

Approval and merge of the Phase-0 PR constitutes acceptance of this specification as the governing scientific input to Phase 1.
