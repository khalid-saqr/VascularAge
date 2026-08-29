# Phase 5 / S2 external execution checklist

1. Open `notebooks/05_s2_robustness.ipynb` from branch `phase-05-s2-robustness` in Google Colab.
2. Select a GPU runtime.
3. Run all cells without editing the notebook source.
4. The notebook must print the exact Phase-5 lock `97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05` and the pinned VascuQuest commit.
5. The runner must verify the preserved Phase-4 folder `/MyDrive/VascularAge/phase_04/locked_trial_amendment001_20260829T153743Z` before computing S2.
6. Phase-5 evidence is written to a new timestamped folder under `/MyDrive/VascularAge/phase_05/`.
7. A successful terminal state prints both `PHASE 5 S2 EXTERNAL EXECUTION: COMPLETE` and `PHASE 5 S2 NOTEBOOK: SUCCESS`.
8. Save the executed notebook back to the same GitHub branch. Do not merge the PR until the saved execution and Drive evidence bundle have been audited.
