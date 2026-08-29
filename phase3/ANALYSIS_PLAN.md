# Phase 3 — Prospectively Locked Confirmatory Analysis Plan

**Project:** The Locked In-Silico Trial Concept  
**Trial title:** *Is Arterial Age Identifiable From the Pulse? An Exhaustive In-Silico Trial of Physiological Aliasing and Measurement Rescue in 4,374 Virtual Subjects*  
**Phase:** 3 — Prospective protocol and code lock  
**Biological endpoint status:** NOT EXECUTED

## 1. Governing rule

Phase 3 freezes the exact confirmatory analysis before any real-PWDB cross-age distance, nearest alias, alias fraction, compensation vector, or measurement-rescue result is calculated. Phase 4 may execute the locked code and configuration but may not alter scientific parameters.

## 2. Population

The qualified design is 4,374 simulations: six age-conditioned groups (25, 35, 45, 55, 65, 75 years), each containing the complete 3^6 factorial over HR, SV, LVET, DIA, PWV, and MAP. `MAP` is represented in the source variation table by `MBP`.

All 4,374 factorial states receive equal design weight. No human-population prevalence is inferred.

## 3. Primary observation and representation

Primary arm P0 is source radial pressure.

For each subject, active source samples are those classified by VascuQuest as neither internal missing nor trailing padding. Phase 1 established zero internal missing radial-pressure samples.

The cardiac period is locked as:

`T_ms = 1000 * N_active / 500`

because the periodic waveform contains `N_active` samples at 500 Hz over phases k/N, k=0,...,N-1.

The complete active cycle is periodically linearly interpolated to 512 uniform phase samples. Absolute pressure in mmHg is retained. No subject-specific mean subtraction, z-score, peak scaling, pulse-pressure scaling, or morphology normalization is permitted.

## 4. Cross-age pair universe

The confirmatory pair universe is exactly the 15 unordered age-pair Cartesian products:

`15 * 729 * 729 = 7,971,615` unordered cross-age pairs.

For every pair, the immutable primary component table stores:
- global row indices i<j;
- radial-pressure phase RMSE in mmHg;
- absolute period difference in ms.

No same-age pair enters the primary alias search.

## 5. Primary aliasing

At pressure tolerance eP and period tolerance eT:

`d = sqrt((RMSE_P/eP)^2 + (DeltaT/eT)^2)`.

A pair aliases if d <= 1.

The prespecified surface is:
- eP = 1, 2, 3, 5, 8, 10 mmHg;
- eT = 2, 5, 10, 20 ms.

The reference operating point is 5 mmHg / 10 ms.

For each source state, the nearest cross-age target is the target minimizing reference d. If multiple targets lie within 1e-6 of the minimum, the canonical target is the smallest global target row index. Tie count is retained.

Primary outputs:
- subject-level D_ref and canonical nearest cross-age state;
- reference alias fraction over all 4,374 states;
- complete 24-point identifiability/alias surface;
- all 15 age-pair directional alias fractions.

## 6. Replication arms

P1: Digital PPG. Since PPG is source dimensionless/arbitrary-unit data, amplitude is not interpreted. Each 512-point PPG cycle is centered and divided by its RMS fluctuation. Shape RMSE is combined elliptically with period difference. Shape tolerances are 0.05, 0.10, 0.20, 0.30, 0.50; reference 0.20. Period grid is the same 2, 5, 10, 20 ms.

P2: Carotid pressure using exactly the P0 pressure/period semantics.

Neither replication arm can replace a failed P0 result.

## 7. Measurement rescue

All rescue arms augment P0 and are strictly nested.

M1 = P0 + Carotid area.  
M2 = M1 + Carotid pressure + reconstructed Carotid flow rate.  
M3 = M2 + AorticRoot P/Q/A + Radial Q/A + Femoral P/Q/A.  
M4 = M3 + P/Q/A at every remaining common site, yielding the complete 13-site common mechanical observation.

The 13 source-supported common sites are:
AorticRoot, ThorAorta, AbdAorta, IliacBif, Carotid, SupTemporal, SupMidCerebral, Brachial, Radial, Digital, CommonIliac, Femoral, AntTibial.

Q is reconstructed on aligned source samples as Q=U*A before phase resampling and retains RECONSTRUCTED semantics.

Additional pressure must satisfy absolute RMSE <= eP. Area and Q use symmetric relative RMS:

`r = RMS(x-y) / sqrt(0.5*(RMS(x)^2 + RMS(y)^2))`.

The relative tolerance grid is 1%, 2%, 5%, 10%, 20%; reference 5%. These are operational tolerance scales, not device-accuracy claims.

A P0-aliased source subject is rescued by arm M if it has no cross-age pair surviving the richer arm at the reference thresholds.

## 8. Physiological compensation

Only P0 reference-aliased sources enter the primary mechanistic compensation analysis.

For each such source:
`Delta xi = xi_target - xi_source`
in locked factor order HR, SV, LVET, DIA, PWV, MAP, using the canonical nearest target.

Mechanistic structure is summarized by the fraction of sources occupied by the 20 most frequent compensation vectors.

Null: 2,000 deterministic Monte-Carlo permutations, seed 20260829. Each aliased source retains its canonical target age, while the target state is drawn uniformly among the 729 factorial states at that age.

If observed top-20 concentration does not exceed the 95th percentile of this null, S4 is triggered.

## 9. Conventional benchmark

The prespecified source quantities are:
- aortic pulse-wave velocity;
- aortic augmentation index;
- brachial systolic pressure.

PWV-only pair alias: symmetric relative PWV difference <=5%.

Composite conventional alias: PWV relative difference <=5%, AIx difference <=5 percentage points, and brachial SBP difference <=5 mmHg.

If PWV-only pair-alias Jaccard with P0 is >=0.90 and subject-level alias-existence agreement is >=0.95, novelty is downgraded under S5.

## 10. Local information geometry

At each age, use the standardized baseline xi=(0,0,0,0,0,0) and the 12 one-factor +/-1 states.

Construct z = [P_phase/(sqrt(512)*5 mmHg), T/(10 ms)].

For each standardized factor k:
`J_k = (z(+1_k)-z(-1_k))/2`.

`F = J^T J`.

Report eigenvalues, eigenvectors, condition number, and weakest direction. It is described as a local information/pullback metric. A Fisher interpretation is allowed only under the corresponding isotropic Gaussian observation model.

## 11. Numerical execution

Production JAX computations use float32 on the accelerator; indices use int32. The primary pair components are stored as float32. Direct waveform differences are used rather than quadratic-distance identities.

A float64 arithmetic audit recomputes nearest reference distances for:
- a deterministic 60-state sample (10 per age);
- every source whose primary D_ref lies within 0.01 of the alias boundary.

An absolute D_ref disagreement >1e-4 or any changed alias classification is a STOP pending explanation.

## 12. Operationalized falsification rules

S1: major aliasing No-Go if alias fraction is <1% at every one of the 24 P0 tolerance points.

S2: assessed in Phase 5. Robust aliasing No-Go if both locked L1-pressure and L-infinity-pressure subject-alias sets have Jaccard <0.50 with P0 at matched 5 mmHg/10 ms scales.

S3: physiological-aliasing No-Go if P0 reference alias fraction is <1% and is <20% of morphology-only (pressure RMSE <=5 mmHg) alias fraction.

S4: mechanistic-compensation No-Go if observed top-20 compensation-motif concentration is <=95th percentile of the locked null.

S5: novelty downgrade if PWV-only pair Jaccard >=0.90 and subject-level alias agreement >=0.95.

S6: measurement-rescue No-Go if every M1-M4 rescue fraction is <10%.

S7: any requirement for a forbidden subject-specific primary normalization invalidates the primary claim.

## 13. Phase-4 output contract

Phase 4 must emit the exact output set listed in `LOCKED_TRIAL_CONFIG.json`, including the primary pair-component table, subject results, tolerance surface, age-pair matrix, replication, compensation, rescue, conventional benchmark, information geometry, numerical audit, execution provenance, and trial summary.

## 14. Change control

After Phase 3 merge:
- scientific parameters in locked files may not be edited before the confirmatory run;
- Phase 4 may add only orchestration, environment setup, and output persistence around the locked runner;
- any scientifically material change requires a numbered protocol amendment, invalidates the unamended confirmatory status for affected endpoints, and must be disclosed;
- exploratory analyses must be labeled exploratory and cannot replace a failed confirmatory endpoint.
