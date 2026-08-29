#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NB=ROOT/"notebooks"/"04_confirmatory_trial.ipynb"
WRAP=ROOT/"scripts"/"phase4_colab.py"
LOCK_SHA="89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
BRANCH="phase-04-confirmatory-execution"

def req(c,m):
    if not c: raise AssertionError(m)

def main():
    nb=json.loads(NB.read_text(encoding="utf-8"))
    req(nb["nbformat"]==4,"notebook format drift")
    for cell in nb["cells"]:
        if cell["cell_type"]=="code":
            req(cell.get("execution_count") is None,"notebook must be unexecuted")
            req(cell.get("outputs")==[],"notebook contains outputs before external run")
    nt="\n".join("".join(c.get("source",[])) for c in nb["cells"])
    for t in (f'BRANCH="{BRANCH}"',f'LOCK_SHA="{LOCK_SHA}"',
              'scripts"/"phase4_colab.py','--execute-locked-trial',
              'phase-04-confirmatory-execution','PHASE 4 LOCKED TRIAL: EXECUTED'):
        req(t in nt,f"missing notebook token: {t}")

    wt=WRAP.read_text(encoding="utf-8")
    for t in (f'LOCK_SHA = "{LOCK_SHA}"','VQ_SHA = "79891036e61df3096536da8f647f2297b0d88252"',
              'scripts"/"phase4_execute_locked.py','--execute-locked-trial',
              'jax.default_backend()','backend!="cpu"',
              'model_variations','haemodynamic_parameters','common_site_waveforms_csv',
              'bundle_hashes.json','external_execution_evidence.json',
              'PHASE 4 LOCKED TRIAL: EXECUTED'):
        req(t in wt,f"missing wrapper token: {t}")
    for t in ("pressure_tolerance_grid_mmHg =","duration_tolerance_grid_ms =",
              "reference_relative_tolerance =","null_permutations =","random_seed ="):
        req(t not in wt,f"wrapper overrides locked science: {t}")
    manifest=json.loads((ROOT/"phase3"/"LOCK_MANIFEST.json").read_text())
    req(manifest["lock_package_sha256"]==LOCK_SHA,"Phase-3 lock mismatch")
    print("Phase 4 external-execution static validation: PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
