#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, select, shlex, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

LOCK_SHA = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
VQ_SHA = "79891036e61df3096536da8f647f2297b0d88252"

def req(c,m):
    if not c: raise AssertionError(m)

def h(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--execute-locked-trial", action="store_true")
    ap.add_argument("--expected-lock-package-sha", required=True)
    ap.add_argument("--drive-root", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--vq-root", required=True)
    args=ap.parse_args()

    req(args.execute_locked_trial, "Phase 4 execution flag required")
    req(args.expected_lock_package_sha == LOCK_SHA, "unexpected lock SHA")

    drive=Path(args.drive_root).resolve()
    repo=Path(args.repo_root).resolve()
    vq=Path(args.vq_root).resolve()
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out=drive/f"locked_trial_{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    manifest=json.loads((repo/"phase3"/"LOCK_MANIFEST.json").read_text())
    req(manifest["lock_package_sha256"]==LOCK_SHA, "manifest lock mismatch")
    basis={"parent_main_commit":manifest["parent_main_commit"],
           "upstream_git_blobs":manifest["upstream_git_blobs"],
           "locked_files_sha256":manifest["locked_files_sha256"],
           "external_qualified_execution":manifest["external_qualified_execution"]}
    computed=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    req(computed==LOCK_SHA, "canonical lock digest mismatch")
    for rel,expected in manifest["locked_files_sha256"].items():
        req(h(repo/rel)==expected, f"locked file drift: {rel}")

    tests=subprocess.run([sys.executable,"-m","pytest","-q"],cwd=repo,text=True,capture_output=True)
    print(tests.stdout)
    if tests.stderr: print(tests.stderr,file=sys.stderr)
    req(tests.returncode==0,"repository tests failed")

    import jax
    backend=jax.default_backend()
    devices=[str(d) for d in jax.devices()]
    print("JAX backend:",backend)
    print("JAX devices:",devices)
    req(backend!="cpu","Phase 4 requires GPU/TPU JAX backend")

    from vascuquest.data import ArtifactAcquirer,DataPaths,SourceRegistry,verify_artifact
    from vascuquest.schema import load_manifest
    paths=DataPaths.default()
    vm=load_manifest()
    reg=SourceRegistry(paths.state_file("sources.json"))
    acq=ArtifactAcquirer(paths,reg,manifest=vm)
    report={}
    for aid in ("model_variations","haemodynamic_parameters","common_site_waveforms_csv"):
        spec=vm.artifact(aid); p=acq.acquire(aid,offline=False); chk=verify_artifact(p,spec)
        req(chk.state.value=="verified",f"artifact not verified: {aid}")
        req(chk.observed_checksum==spec.checksum_value,f"artifact checksum mismatch: {aid}")
        report[aid]={"filename":spec.filename,"path":str(p),"checksum":chk.observed_checksum,"size_bytes":chk.size_bytes}
        print("VERIFIED",aid,p)
    (out/"source_preflight.json").write_text(json.dumps(report,indent=2))

    vq_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=vq,text=True).strip()
    req(vq_commit==VQ_SHA,"VascuQuest commit mismatch")
    va_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()

    runner=repo/"scripts"/"phase4_execute_locked.py"
    cmd=[sys.executable,str(runner),"--execute-locked-trial","--expected-lock-package-sha",LOCK_SHA,
         "--repo-root",str(repo),"--pwdb-root",str(paths.source),"--output-root",str(out)]
    print("Executing:", " ".join(shlex.quote(x) for x in cmd))
    logp=out/"phase4_console.log"; start=time.time(); hb=start
    with logp.open("w",encoding="utf-8") as log:
        proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        while proc.poll() is None:
            ready,_,_=select.select([proc.stdout],[],[],1.0)
            if ready:
                line=proc.stdout.readline()
                if line:
                    print(line,end="",flush=True); log.write(line); log.flush()
            now=time.time()
            if now-hb>=60:
                files=sorted(p.name for p in out.iterdir())
                msg=f"[heartbeat] elapsed={int(now-start)}s files={len(files)} latest={files[-5:]}"
                print(msg,flush=True); log.write(msg+"\n"); log.flush(); hb=now
        for line in proc.stdout:
            print(line,end="",flush=True); log.write(line)
    req(proc.returncode==0,f"locked runner failed: {proc.returncode}")

    cfg=json.loads((repo/"phase3"/"LOCKED_TRIAL_CONFIG.json").read_text())
    required=list(cfg["phase4_outputs"])
    missing=[x for x in required if not (out/x).exists()]
    req(not missing,f"missing locked outputs: {missing}")
    summary=json.loads((out/"trial_summary.json").read_text())
    prov=json.loads((out/"execution_provenance.json").read_text())
    audit=json.loads((out/"numerical_audit.json").read_text())
    req(summary["phase"]==4 and summary["status"]=="EXECUTED","summary status failure")
    req(summary["lock_package_sha256"]==LOCK_SHA,"summary lock mismatch")
    req(summary["subjects"]==4374 and summary["unordered_cross_age_pairs"]==7971615,"trial cardinality drift")
    req(prov["jax_backend"]!="cpu","non-accelerated execution")
    req(audit["max_abs_D_ref_difference"]<=1e-4,"numerical audit failed")

    hashes={x:h(out/x) for x in required}
    (out/"bundle_hashes.json").write_text(json.dumps(hashes,indent=2,sort_keys=True))
    evidence={"phase":4,"status":"EXECUTED","lock_package_sha256":LOCK_SHA,
              "vascularage_execution_commit":va_commit,"vascuquest_commit":vq_commit,
              "jax_backend":prov["jax_backend"],"jax_devices":devices,
              "output_root":str(out),"bundle_hashes":hashes,
              "trial_summary":summary,
              "numerical_audit":{"subjects_audited":audit["subjects_audited"],
                                  "max_abs_D_ref_difference":audit["max_abs_D_ref_difference"]}}
    (out/"external_execution_evidence.json").write_text(json.dumps(evidence,indent=2))
    print("="*76)
    print("PHASE 4 LOCKED TRIAL: EXECUTED")
    print("="*76)
    print(json.dumps(summary,indent=2))
    print("Numerical audit:",evidence["numerical_audit"])
    print("Evidence bundle:",out)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
