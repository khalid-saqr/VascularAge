# Phase 2 — Systematic evidence map and novelty collision audit

**Status:** completed evidence synthesis; no biological trial endpoint executed.

Phase 2 maps a frozen 889-record Scopus corpus and supplements it with a targeted current collision audit focused on the locked trial's actual inverse-problem novelty.

Key outputs:
- `CORPUS_MANIFEST.json` — cryptographic identity and limitations of the frozen corpus.
- `ontology.json` — transparent evidence-map axes, bit order, and collision definitions.
- `evidence_map/evidence_map_01.csv` … `_04.csv` — compact complete 889-record map; one row per frozen source row, with a hexadecimal evidence-axis bitmask.
- `collision_audit/collision_audit_01.csv` … `_04.csv` — all 111 high-relevance title/abstract adjudications by frozen source row index.
- `negative_control_audit_50.csv` — seeded audit outside the high-relevance set.
- `external_collision_audit.csv` — source-checked current identifiability/inverse-problem neighbours.
- `TARGETED_SEARCH_LOG.md` — exact current collision-search queries.
- `NOVELTY_STATEMENT.md` — claim boundary handed to Phase 3.
- `REVIEW_LIMITATIONS.md` — mandatory limitations.
- `summary.json` — machine-readable counts and status.

The raw Scopus export and abstracts are not redistributed in Git. `CORPUS_MANIFEST.json` cryptographically identifies the frozen source and defines its canonical row order, so every compact row index is reproducible when the licensed/source export is available.

No meta-analysis was performed because no defensible common quantitative estimand exists across this heterogeneous literature.
