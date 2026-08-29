# Execute Phase 5 / S2 in Colab

Open `notebooks/05_s2_robustness.ipynb` from branch `phase-05-s2-robustness`, select a GPU runtime, and run all cells unchanged.

The notebook clones the exact branch, verifies S2 lock `97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05`, checks the pinned VascuQuest commit, verifies the preserved Phase-4 A001 evidence folder, runs the guarded S2 endpoint, and writes a new timestamped evidence bundle under `/MyDrive/VascularAge/phase_05/`.

After successful execution, save the executed notebook back to the same branch for audit. Do not merge the Phase-5 PR before that audit is complete.
