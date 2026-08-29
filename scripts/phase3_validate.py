#!/usr/bin/env python3
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P3=ROOT/"phase3"

def req(c,m):
    if not c: raise AssertionError(m)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_lock_basis(manifest):
    return {
        "parent_main_commit":manifest["parent_main_commit"],
        "upstream_git_blobs":manifest["upstream_git_blobs"],
        "locked_files_sha256":manifest["locked_files_sha256"],
        "external_qualified_execution":manifest["external_qualified_execution"],
    }

def main():
    cfg=json.loads((P3/"LOCKED_TRIAL_CONFIG.json").read_text())
    man=json.loads((P3/"LOCK_MANIFEST.json").read_text())
    req(cfg["phase"]==3 and cfg["biological_endpoints_allowed_in_phase3"] is False,"phase3 biological guard")
    req(cfg["parent_main_commit"]=="fabaa7b9fa6564bbca21e020c6522cf2e5b16bab","parent main drift")
    req(cfg["dataset"]["expected_subjects"]==4374 and cfg["dataset"]["subjects_per_age"]==729,"population drift")
    req(len(cfg["dataset"]["ages"])==6 and len(cfg["dataset"]["factor_order"])==6,"design drift")
    req(15*729*729==7971615,"pair-universe arithmetic")
    req(len(cfg["primary"]["pressure_tolerance_grid_mmHg"])*len(cfg["primary"]["duration_tolerance_grid_ms"])==24,"primary surface drift")
    req(cfg["primary"]["reference"]=={"pressure_mmHg":5.0,"duration_ms":10.0},"reference tolerance drift")
    req(cfg["waveform_representation"]["cycle_duration_ms_formula"]=="1000 * active_sample_count / sample_rate_hz","period convention drift")
    req(cfg["measurement_rescue"]["evaluation_order"]==["M1","M2","M3","M4"],"rescue order drift")
    common=cfg["measurement_rescue"]["arms"]["M4"]["sites_all_common"]; req(len(common)==13 and len(set(common))==13,"common-site lock drift")
    req(cfg["compensation"]["random_seed"]==20260829 and cfg["compensation"]["null_permutations"]==2000,"compensation null drift")
    req(cfg["numerics"]["production_dtype"]=="float32" and cfg["numerics"]["tie_atol"]==1e-6,"numeric lock drift")
    for rel,h in man["locked_files_sha256"].items():
        req((ROOT/rel).exists(),f"locked file missing {rel}"); req(sha(ROOT/rel)==h,f"locked file hash drift {rel}")
    basis=canonical_lock_basis(man)
    digest=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    req(digest==man["lock_package_sha256"],"lock package digest drift")
    req(man["external_qualified_execution"]["phase1_status"]=="PASS","Phase1 qualification not bound")
    req(man["external_qualified_execution"]["biological_endpoint_executed"] is False,"prior biological leakage")
    req(man["upstream_git_blobs"]["phase2/NOVELTY_STATEMENT.md"]=="2aaf891fe500c710f3850a351893c3dd6d463bc5","novelty blob drift")
    runner=(ROOT/"scripts"/"phase4_execute_locked.py").read_text()
    ast.parse(runner)
    req("--execute-locked-trial" in runner and "--expected-lock-package-sha" in runner,"execution guards missing")
    req("if __name__==\"__main__\"" in runner or "if __name__ == \"__main__\"" in runner,"runner main guard missing")
    for name in cfg["phase4_outputs"]:
        req(not (P3/name).exists(),f"biological result leaked into Phase3: {name}")
    print("Phase 3 prospective lock validation: PASS")
    print(json.dumps({"lock_package_sha256":man["lock_package_sha256"],"biological_endpoint_executed":False,
                      "unordered_cross_age_pairs":7971615,"tolerance_points":24},sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
