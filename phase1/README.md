# Phase 1 — Rebuilt external Colab qualification

This phase qualifies the canonical PWDB/VascuQuest source boundary and the synthetic JAX numerical engine **without executing any biological cross-age endpoint**.

Open in Colab:

https://colab.research.google.com/github/khalid-saqr/VascularAge/blob/phase-01-engine-qualification/notebooks/01_engine_qualification.ipynb

Run **Runtime → Run all**, authorize Google Drive, change nothing, and save the executed notebook with outputs back to the same branch/path.

Persistent storage: `/content/drive/MyDrive/VascularAge/phase_01`

Pinned VascuQuest: `79891036e61df3096536da8f647f2297b0d88252`

The exact Phase-1 contract SHA-256 is computed from repository bytes during execution and recorded together with the executed VascularAge and VascuQuest commit SHAs. Phase 3 remains the prospective external protocol-hash lock point.

The qualification bundle is written under `qualification_v2/` in Google Drive. Raw PWDB artifacts remain outside Git.
