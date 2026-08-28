# Phase 0 Validation Record

**Phase:** 0 — Canonical trial specification  
**Validation target:** Internal consistency and scientific boundary checks only  
**Biological endpoint execution:** PROHIBITED / NOT PERFORMED

## Checks required before commit

1. Machine-readable YAML files parse successfully.
2. All YAML files declare `schema_version: "1.0"` and `phase: 0`.
3. Expected population arithmetic is internally consistent: 6 × 729 = 4,374 and 729 = 3^6.
4. Primary site is `Radial` and primary quantity is pressure in both protocol and YAML.
5. Primary phase representation uses 512 samples and preserves absolute amplitude.
6. Reference scales are 5 mmHg and 10 ms in protocol, estimands, and uncertainty model.
7. Pressure tolerance grid contains the reference 5-mmHg point.
8. Cycle-duration tolerance grid contains the reference 10-ms point.
9. `P0` is the primary observation arm.
10. Reconstructed flow is explicitly marked `RECONSTRUCTED`.
11. Falsification rules include methodological STOP rules and scientific No-Go/downgrade rules.
12. No file describes the 4,374 simulations as human patients/participants.
13. No Phase-4 cross-age biological result, alias prevalence, or age-pair output is present.
14. No large PWDB data file or result cache is added.
15. Phase-1 source verification is mandatory before biological execution.

## Scope audit

Phase 0 intentionally leaves the following as Layer-B technical choices:
- exact source field names for the six factorial coordinates;
- exact non-pressure modality tolerance operators;
- exact restricted multisite membership for arm M3;
- numerical JAX batching and precision policy;
- stochastic robustness distributions.

These items may be resolved only from source semantics, software verification, or external measurement evidence. They may not be selected using the substantive cross-age aliasing results and must be frozen by Phase 3.

## Acceptance

A merged Phase-0 PR means the project owner accepts the scientific specification as the governing input to Phase 1. It does not imply that the hypothesized aliasing phenomenon exists.
