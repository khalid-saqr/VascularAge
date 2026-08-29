#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AMENDMENT_LOCK_SHA = "1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7"
ORIGINAL_LOCK_SHA = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
VQ_SHA = "79891036e61df3096536da8f647f2297b0d88252"
REFERENCE_RUN_NAME = "locked_trial_20260829T131721Z"


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute-amendment001-trial", action="store_true")
    ap.add_argument("--expected-amendment-lock-sha", required=True)
    ap.add_argument("--drive-root", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--vq-root", required=True)
    args = ap.parse_args()

    req(args.execute_amendment001_trial, "A001 execution flag required")
    req(args.expected_amendment_lock_sha == AMENDMENT_LOCK_SHA, "unexpected A001 lock SHA")

    drive = Path(args.drive_root).resolve()
    repo = Path(args.repo_root).resolve()
    vq = Path(args.vq_root).resolve()
    reference = drive / REFERENCE_RUN_NAME
    req(reference.is_dir(), f"preserved P0 reference run missing: {reference}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = drive / f"locked_trial_amendment001_{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    amendment = json.loads((repo / "phase4" / "AMENDMENT_001_LOCK.json").read_text())
    req(amendment["amendment_lock_sha256"] == AMENDMENT_LOCK_SHA, "A001 manifest lock mismatch")
    basis = amendment["canonical_basis"]
    computed = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    req(computed == AMENDMENT_LOCK_SHA, "A001 canonical lock digest mismatch")
    for rel, expected in basis["amended_files_sha256"].items():
        req(h(repo / rel) == expected, f"A001 file drift: {rel}")

    original = json.loads((repo / "phase3" / "LOCK_MANIFEST.json").read_text())
    req(original["lock_package_sha256"] == ORIGINAL_LOCK_SHA, "original lock mismatch")
    for rel, expected in original["locked_files_sha256"].items():
        req(h(repo / rel) == expected, f"original locked file drift: {rel}")

    tests = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=repo, text=True, capture_output=True)
    print(tests.stdout)
    if tests.stderr:
        print(tests.stderr, file=sys.stderr)
    req(tests.returncode == 0, "repository tests failed")

    import jax
    backend = jax.default_backend()
    devices = [str(d) for d in jax.devices()]
    print("JAX backend:", backend)
    print("JAX devices:", devices)
    req(backend != "cpu", "Phase 4 Amendment 001 requires GPU/TPU JAX backend")

    from vascuquest.data import ArtifactAcquirer, DataPaths, SourceRegistry, verify_artifact
    from vascuquest.schema import load_manifest

    paths = DataPaths.default()
    vm = load_manifest()
    reg = SourceRegistry(paths.state_file("sources.json"))
    acq = ArtifactAcquirer(paths, reg, manifest=vm)
    report = {}
    for aid in ("model_variations", "haemodynamic_parameters", "common_site_waveforms_csv"):
        spec = vm.artifact(aid)
        path = acq.acquire(aid, offline=False)
        chk = verify_artifact(path, spec)
        req(chk.state.value == "verified", f"artifact not verified: {aid}")
        req(chk.observed_checksum == spec.checksum_value, f"artifact checksum mismatch: {aid}")
        report[aid] = {
            "filename": spec.filename,
            "path": str(path),
            "checksum": chk.observed_checksum,
            "size_bytes": chk.size_bytes,
        }
        print("VERIFIED", aid, path)
    (out / "source_preflight.json").write_text(json.dumps(report, indent=2))

    vq_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vq, text=True).strip()
    req(vq_commit == VQ_SHA, "VascuQuest commit mismatch")
    va_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    runner = repo / "scripts" / "phase4_execute_amendment001.py"
    cmd = [
        sys.executable, str(runner),
        "--execute-amendment001-trial",
        "--expected-amendment-lock-sha", AMENDMENT_LOCK_SHA,
        "--repo-root", str(repo),
        "--pwdb-root", str(paths.source),
        "--reference-p0-root", str(reference),
        "--output-root", str(out),
    ]
    print("Executing:", " ".join(shlex.quote(x) for x in cmd))
    logp = out / "phase4_console.log"
    start = time.time()
    heartbeat = start
    with logp.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        while proc.poll() is None:
            ready, _, _ = select.select([proc.stdout], [], [], 1.0)
            if ready:
                line = proc.stdout.readline()
                if line:
                    print(line, end="", flush=True)
                    log.write(line)
                    log.flush()
            now = time.time()
            if now - heartbeat >= 60:
                files = sorted(p.name for p in out.iterdir())
                msg = f"[heartbeat] elapsed={int(now-start)}s files={len(files)} latest={files[-6:]}"
                print(msg, flush=True)
                log.write(msg + "\n")
                log.flush()
                heartbeat = now
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)

    if proc.returncode != 0:
        failure = out / "execution_failure.json"
        if failure.exists():
            print("Structured failure evidence:")
            print(failure.read_text())
        raise AssertionError(f"A001 runner failed: {proc.returncode}")

    cfg = json.loads((repo / "phase3" / "LOCKED_TRIAL_CONFIG.json").read_text())
    required = list(cfg["phase4_outputs"])
    required += ["waveform_alignment_audit.json", "p0_reproducibility_gate.json"]
    missing = [name for name in required if not (out / name).exists()]
    req(not missing, f"missing A001 outputs: {missing}")

    summary = json.loads((out / "trial_summary.json").read_text())
    provenance = json.loads((out / "execution_provenance.json").read_text())
    audit = json.loads((out / "numerical_audit.json").read_text())
    p0_gate = json.loads((out / "p0_reproducibility_gate.json").read_text())
    req(summary["phase"] == 4 and summary["status"] == "EXECUTED_AMENDMENT_001", "summary status failure")
    req(summary["amendment_lock_sha256"] == AMENDMENT_LOCK_SHA, "summary A001 lock mismatch")
    req(summary["original_phase3_lock_sha256"] == ORIGINAL_LOCK_SHA, "summary original lock mismatch")
    req(summary["subjects"] == 4374 and summary["unordered_cross_age_pairs"] == 7971615, "trial cardinality drift")
    req(provenance["jax_backend"] != "cpu", "non-accelerated execution")
    req(audit["max_abs_D_ref_difference"] <= 1e-4, "numerical audit failed")
    req(p0_gate["status"] == "PASS", "P0 reproducibility gate failed")

    hashes = {name: h(out / name) for name in required}
    (out / "bundle_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True))
    evidence = {
        "phase": 4,
        "status": "EXECUTED_AMENDMENT_001",
        "amendment_id": "A001",
        "amendment_lock_sha256": AMENDMENT_LOCK_SHA,
        "original_phase3_lock_sha256": ORIGINAL_LOCK_SHA,
        "vascularage_execution_commit": va_commit,
        "vascuquest_commit": vq_commit,
        "jax_backend": provenance["jax_backend"],
        "jax_devices": devices,
        "reference_p0_root": str(reference),
        "output_root": str(out),
        "bundle_hashes": hashes,
        "trial_summary": summary,
        "numerical_audit": {
            "subjects_audited": audit["subjects_audited"],
            "max_abs_D_ref_difference": audit["max_abs_D_ref_difference"],
        },
        "p0_reproducibility_gate": p0_gate,
    }
    (out / "external_execution_evidence.json").write_text(json.dumps(evidence, indent=2))
    print("=" * 76)
    print("PHASE 4 AMENDMENT 001 TRIAL: EXECUTED")
    print("=" * 76)
    print(json.dumps(summary, indent=2))
    print("Numerical audit:", evidence["numerical_audit"])
    print("P0 reproducibility gate: PASS")
    print("Evidence bundle:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())