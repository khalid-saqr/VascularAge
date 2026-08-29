#!/usr/bin/env python3
"""Phase-4 completion under formal post-P0 Protocol Amendment 001.

The original Phase-3 runner is imported unchanged and remains the execution
authority for every scientific operator.  A001 adds only: (1) site-local
source-support semantics, (2) complete waveform-support preflight, (3) an
early P0 float64 audit and preserved-P0 reproducibility gate, and (4) explicit
amendment provenance/failure evidence.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

from vascularage.locked_io import duration_vector_from_counts, load_variations, load_waveform_matrix
from vascularage.amendment001_io import (
    audit_common_site_waveforms,
    load_flow_rate_matrix_site_local,
)

ORIGINAL_LOCK_SHA="89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
REFERENCE_RUN_NAME="locked_trial_20260829T131721Z"

def req(c,m):
    if not c: raise AssertionError(m)

def h(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_locked(repo:Path):
    p=repo/"scripts"/"phase4_execute_locked.py"
    spec=importlib.util.spec_from_file_location("phase4_original_locked",p)
    req(spec is not None and spec.loader is not None,"cannot load original locked runner")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def validate_a001(repo:Path,expected:str):
    m=json.loads((repo/"phase4"/"AMENDMENT_001_LOCK.json").read_text())
    req(m["amendment_lock_sha256"]==expected,"A001 lock SHA mismatch")
    b=m["canonical_basis"]
    calc=hashlib.sha256(json.dumps(b,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    req(calc==expected,"A001 canonical digest mismatch")
    req(b["original_phase3_lock_sha256"]==ORIGINAL_LOCK_SHA,"original-lock identity drift")
    for rel,expected_hash in b["amended_files_sha256"].items():
        req(h(repo/rel)==expected_hash,f"A001 locked file drift: {rel}")
    return m

def verify_reference(root:Path,hashes:dict):
    req(root.name==REFERENCE_RUN_NAME,"unexpected P0 reference directory")
    for name,expected in hashes.items():
        p=root/name; req(p.exists(),f"missing preserved P0 artifact: {name}")
        req(h(p)==expected,f"preserved P0 artifact drift: {name}")

def compare_p0(reference:Path,out:Path,hashes:dict):
    verify_reference(reference,hashes)
    for name in ("primary_subject_results.csv","primary_tolerance_surface.csv","primary_age_pair_matrix.csv"):
        req((out/name).read_bytes()==(reference/name).read_bytes(),f"P0 reproducibility failure: {name}")
    old=np.load(reference/"primary_pair_components.npz"); new=np.load(out/"primary_pair_components.npz")
    keys={"i","j","pressure_rmse_mmHg","duration_diff_ms"}
    req(set(old.files)==keys and set(new.files)==keys,"P0 pair schema drift")
    req(np.array_equal(old["i"],new["i"]),"P0 i-index drift")
    req(np.array_equal(old["j"],new["j"]),"P0 j-index drift")
    req(np.array_equal(old["duration_diff_ms"],new["duration_diff_ms"]),"P0 duration-component drift")
    d=float(np.max(np.abs(old["pressure_rmse_mmHg"].astype(np.float64)-new["pressure_rmse_mmHg"].astype(np.float64))))
    req(d<=1e-4,f"P0 pressure-RMSE drift: {d}")
    return {"status":"PASS","reference_run":str(reference),"reference_artifact_sha256":hashes,
            "csv_bytes_exact":True,"pair_indices_exact":True,"duration_diff_exact":True,
            "max_abs_pressure_rmse_difference":d,"pressure_rmse_tolerance":1e-4}

def write_p0_precheck(locked,repo:Path,pwdb:Path,out:Path,reference:Path,hashes:dict):
    ages,xi=load_variations(pwdb/"pwdb_model_variations.csv")
    radial,counts=load_waveform_matrix(pwdb/"PWs_csv.zip","Radial","P")
    durations=duration_vector_from_counts(counts)
    audit52=audit_common_site_waveforms(pwdb/"PWs_csv.zip",counts)
    (out/"waveform_alignment_audit.json").write_text(json.dumps(audit52,indent=2))
    i,j,dp,dt=locked.all_pair_components_jax(radial,durations,ages)
    req(len(i)==7971615,"P0 pair cardinality drift")
    np.savez_compressed(out/"primary_pair_components.npz",i=i,j=j,pressure_rmse_mmHg=dp,duration_diff_ms=dt)
    dref=locked.reference_pair_distance(dp,dt); best,target,ties=locked.canonical_nearest_from_pairs(4374,i,j,dref)
    ref_pair=dref<=1.0; surface=locked.alias_surface(i,j,dp,dt)
    locked.write_csv(out/"primary_tolerance_surface.csv",["pressure_tolerance_mmHg","duration_tolerance_ms","alias_pairs","subjects_with_alias","alias_fraction"],
      [{"pressure_tolerance_mmHg":ep,"duration_tolerance_ms":et,"alias_pairs":p,"subjects_with_alias":s,"alias_fraction":f} for ep,et,p,s,f in surface])
    rows=locked.primary_age_pair_rows(ages,i,j,ref_pair); locked.write_csv(out/"primary_age_pair_matrix.csv",list(rows[0]),rows)
    subj=[]
    for s in range(4374):
        subj.append({"subject_id":s+1,"age":int(ages[s]),**{f:int(xi[s,k]) for k,f in enumerate(locked.FACTOR_ORDER)},
                     "D_ref":float(best[s]),"nearest_subject_id":int(target[s])+1,"nearest_age":int(ages[target[s]]),
                     "tie_count":int(ties[s]),"reference_alias":bool(best[s]<=1.0)})
    locked.write_csv(out/"primary_subject_results.csv",list(subj[0]),subj)
    audit=locked.numerical_audit(radial,durations,ages,best,target)
    (out/"numerical_audit.json").write_text(json.dumps(audit,indent=2))
    gate=compare_p0(reference,out,hashes); gate["numerical_audit"]={"subjects_audited":audit["subjects_audited"],"max_abs_D_ref_difference":audit["max_abs_D_ref_difference"]}
    (out/"p0_reproducibility_gate.json").write_text(json.dumps(gate,indent=2))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--execute-amendment001-trial",action="store_true")
    ap.add_argument("--expected-amendment-lock-sha",required=True)
    ap.add_argument("--repo-root",required=True); ap.add_argument("--pwdb-root",required=True)
    ap.add_argument("--reference-p0-root",required=True); ap.add_argument("--output-root",required=True)
    args=ap.parse_args(); req(args.execute_amendment001_trial,"A001 execution flag required")
    repo=Path(args.repo_root).resolve(); pwdb=Path(args.pwdb_root).resolve(); reference=Path(args.reference_p0_root).resolve(); out=Path(args.output_root).resolve(); out.mkdir(parents=True,exist_ok=True)
    try:
        a001=validate_a001(repo,args.expected_amendment_lock_sha); locked=load_locked(repo); locked.validate_lock(repo,ORIGINAL_LOCK_SHA)
        write_p0_precheck(locked,repo,pwdb,out,reference,a001["canonical_basis"]["reference_p0_artifact_sha256"])
        # Inject only A001 data semantics into the unchanged original runner.
        original_load=locked.load_waveform_matrix
        locked.load_waveform_matrix=lambda archive,site,signal,expected_active_counts=None: original_load(archive,site,signal)
        locked.load_flow_rate_matrix=lambda archive,site,expected_active_counts: load_flow_rate_matrix_site_local(archive,site)[0]
        argv=sys.argv[:]
        sys.argv=[str(repo/"scripts"/"phase4_execute_locked.py"),"--execute-locked-trial","--expected-lock-package-sha",ORIGINAL_LOCK_SHA,
                  "--repo-root",str(repo),"--pwdb-root",str(pwdb),"--output-root",str(out)]
        try: rc=locked.main()
        finally: sys.argv=argv
        req(rc==0,"original locked runner returned nonzero")
        summary=json.loads((out/"trial_summary.json").read_text()); summary.update({"status":"EXECUTED_AMENDMENT_001","amendment_id":"A001",
          "amendment_lock_sha256":args.expected_amendment_lock_sha,"original_phase3_lock_sha256":ORIGINAL_LOCK_SHA,"P0_reproducibility_gate":"PASS"})
        (out/"trial_summary.json").write_text(json.dumps(summary,indent=2))
        prov=json.loads((out/"execution_provenance.json").read_text()); prov["amendment_lock_manifest"]=a001; prov["reference_p0_root"]=str(reference)
        (out/"execution_provenance.json").write_text(json.dumps(prov,indent=2))
        return 0
    except Exception as exc:
        if (out/"p0_reproducibility_gate.json").exists(): stage="after_P0_reproducibility_gate"
        elif (out/"numerical_audit.json").exists(): stage="P0_audit_or_reproducibility_gate"
        elif (out/"waveform_alignment_audit.json").exists(): stage="after_waveform_preflight"
        else: stage="initialization"
        (out/"execution_failure.json").write_text(json.dumps({"phase":4,"amendment_id":"A001","status":"FAILED","stage":stage,
          "exception_type":type(exc).__name__,"exception_message":str(exc),"files_present":sorted(p.name for p in out.iterdir())},indent=2))
        raise

if __name__=="__main__": raise SystemExit(main())