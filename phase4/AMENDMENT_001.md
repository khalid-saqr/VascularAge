# Phase 4 — Protocol Amendment 001

## Site-local waveform sampling semantics

**Amendment ID:** A001  
**Original Phase-3 lock:** `89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963`  
**Original execution code:** `07c10ee428f43a91036af7cb2efcb8d4b05bb734`  
**Failed executed-notebook commit:** `9a7cd75e227f1589f78031535252db9608fa9e64`

## 1. Why the amendment is required

The first Phase-4 execution passed the Phase-3 lock, source-integrity, repository-test and accelerator gates and completed P0. It then stopped at P1 because the Phase-3 implementation required the Digital PPG raw active-sample count to equal the P0 Radial-pressure raw active-sample count for every subject.

The canonical PWDB source does not support that cross-site equality assumption. Its common-site waveforms have valid site-local active supports; site-to-site support lengths may differ by one or occasionally two samples. This is compatible with the locked scientific design because all waveform morphology comparisons occur after periodic resampling to the common 512-point phase domain.

The cross-site raw-count equality was an implementation invariant, not a scientific estimand or protocol requirement.

## 2. Outcome disclosure boundary

This amendment is adopted **after** P0 was revealed. The original run `locked_trial_20260829T131721Z` produced:

- 53,842 P0 reference alias pairs;
- 2,764 / 4,374 source states with at least one P0 reference alias;
- P0 reference alias fraction `0.6319158664837677`;
- the complete P0 pair-component table, subject results, tolerance surface and age-pair matrix.

Before this amendment, the following substantive outputs had **not** been obtained: P1, P2, compensation vectors/motifs/null, M1–M4 rescue, conventional benchmark, information geometry, float64 numerical audit and final falsification adjudication.

No claim is made that A001 is prospective relative to P0. It is locked before re-execution of all still-unseen secondary and mechanistic endpoints.

## 3. Primary endpoint is immutable

A001 does **not** alter any P0 scientific definition:

- complete 4,374-state population;
- all 7,971,615 unordered cross-age pairs;
- Radial pressure as P0;
- P0 active-sample and padding semantics;
- 512-point periodic interpolation;
- subject duration `T = 1000 * N_active(Radial P) / 500`;
- 24-point tolerance surface;
- reference 5 mmHg / 10 ms operating point;
- pair-distance formula;
- nearest-target and tie-breaking rules;
- forbidden P0 normalizations.

## 4. Refined amended rule

The amended source rule is deliberately minimal:

> **No cross-signal raw-length equality is required unless a mathematical operation itself requires aligned source samples.**

Therefore:

1. Pressure, area and PPG waveforms are each validated on their own source-supported active cycle and independently phase-resampled to 512 points.
2. Raw active-count equality across anatomical sites is not required.
3. Raw active-count equality among unrelated signals is not required.
4. The trial's duration coordinate remains defined exclusively by P0 Radial pressure. P1 and P2 continue to use the already-locked P0 duration difference.
5. For reconstructed flow `Q=U*A`, U and A must have identical local sample support because the multiplication is pointwise. Q is formed on those local source samples and only then phase-resampled.
6. No trimming, padding, forced raw-grid registration, new site-specific duration definition, or change to any tolerance is permitted.

## 5. New gates added by A001

Before downstream biological endpoints are allowed:

- all 52 common-site waveform members are audited;
- every member must contain all 4,374 subjects under the qualified missing/padding semantics;
- cross-site active-count differences are recorded and explicitly permitted;
- local U/A support equality is required at every reconstruction site;
- P0 is recomputed with the original locked P0 implementation;
- the float64 P0 audit is executed immediately after P0;
- the four preserved original P0 artifacts are checksum-verified;
- amended-run P0 must reproduce the preserved P0 pair components, subject table, tolerance surface and age-pair matrix before P1 is allowed to execute.

Any failure of the P0 reproducibility gate is an immediate STOP.

## 6. Preserved P0 evidence

The preserved original P0 artifact SHA-256 values are machine-locked in `phase4/AMENDMENT_001_PROTOCOL.json` and in the A001 lock manifest.

The original failed execution directory must remain untouched:

`/content/drive/MyDrive/VascularAge/phase_04/locked_trial_20260829T131721Z`

The amended run writes to a new directory and never overwrites the original evidence.

## 7. Change-control classification

A001 is classified as a **post-P0 implementation amendment**. It corrects an over-constrained source-loader invariant while preserving P0 and every predeclared downstream scientific tolerance/operator. The original Phase-3 lock remains immutable and is incorporated by reference into the A001 cryptographic lock.
