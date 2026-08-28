#!/usr/bin/env python3
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "phase1" / "qualification_contract.json"
NOTEBOOK = ROOT / "notebooks" / "01_engine_qualification.ipynb"
RUNNER = ROOT / "scripts" / "phase1_colab.py"


def require(x, msg):
    if not x:
        raise AssertionError(msg)


def main():
    contract_bytes = CONTRACT.read_bytes()
    sha = hashlib.sha256(contract_bytes).hexdigest()
    contract = json.loads(contract_bytes)
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    meta = nb.get("metadata", {}).get("vascularage", {})
    require(meta.get("phase") == 1, "notebook phase mismatch")
    require(meta.get("contract_version") == contract["contract_version"], "notebook contract version mismatch")
    require(meta.get("biological_endpoints_allowed") is False, "notebook biological guard mismatch")
    require(meta.get("vascuquest_commit") == contract["vascuquest"]["commit_sha"], "notebook VascuQuest commit mismatch")

    code = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            ast.parse(src)
            code.append(src)
    joined = "\n".join(code)
    for token in ["ALLOW_BIOLOGICAL_ENDPOINTS = False", "phase-01-engine-qualification", contract["drive_root"], "phase1_colab.py", "contract_sha"]:
        require(token in joined, f"notebook missing {token}")
    for token in ["ghp_", "github_pat_", "GITHUB_TOKEN", "git push", "git remote set-url"]:
        require(token not in joined, f"forbidden notebook token {token}")

    runner = RUNNER.read_text(encoding="utf-8")
    ast.parse(runner)
    require("ALLOW_BIOLOGICAL_ENDPOINTS = False" in runner, "runner guard missing")
    require("synthetic_qualification()" in runner, "runner synthetic qualification missing")
    require("observed_contract_sha = hashlib.sha256(contract_bytes).hexdigest()" in runner, "runtime contract hash recording missing")
    require("--expected-contract-sha" not in runner, "runner still contains circular contract hash gate")
    require("nearest_cross_age_numpy(" not in runner and "nearest_cross_age_jax(" not in runner,
            "runner must not call nearest-search functions directly on source data")
    require(contract["source"]["model_variations_exact_header"] ==
            ["SUBJECT NUMBER","AGE","DIA","HR","LVET","MBP","PWV","SV"], "source schema drift")
    require("contract_hash_recorded" in contract["qualification_layers"]["D_provenance"], "provenance gate drift")
    print("Phase-1 rebuild static validation: PASS")
    print("Observed contract SHA-256 (recorded at runtime):", sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
