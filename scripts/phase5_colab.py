#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

S2_LOCK_SHA = "97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05"
ORIGINAL_PHASE3_LOCK = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
A001_LOCK = "1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7"
VQ_SHA = "79891036e61df3096536da8f647f2297b0d88252"
PHASE4_REFERENCE = "locked_trial_amendment001_20260829T153743Z"


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute-s2", action="store_true")
    ap.add_argument("--expected-s2-lock-sha", required=True)
    ap.add_argument("--phase4-root", required=True)
    ap.add_argument("--output-parent", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--vq-root", required=True)
    args = ap.parse_args()

    req(args.execute_s2, "Phase-5 S2 execution flag required")
    req(args.expected_s2_lock_sha == S2_LOCK_SHA, "unexpected S2 lock SHA")

    phase4 = Path(args.phase4_root).resolve()
    output_parent = Path(args.output_parent).resolve()
    repo = Path(args.repo_root).resolve()
    vq = Path(args.vq_root).resolve()
    req(phase4.name == PHASE4_REFERENCE and phase4.is_dir(), f"Phase-4 evidence folder missing/mismatched: {phase4}")
    output_parent.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((repo / "phase5" / "S2_LOCK.json").read_text())
    req(manifest["s2_lock_sha256"] == S2_LOCK_SHA, "Phase-5 lock manifest mismatch")
    basis = manifest["canonical_basis"]
    calc = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    req(calc == S2_LOCK_SHA, "Phase-5 lock digest mismatch")
    for rel, expected in basis["locked_files_sha256"].items():
        req(h(repo / rel) == expected, f"Phase-5 locked file drift: {rel}")

    p3 = json.loads((repo / "phase3" / "LOCK_MANIFEST.json").read_text())
    req(p3["lock_package_sha256"] == ORIGINAL_PHASE3_LOCK, "Phase-3 lock mismatch")
    a001 = json.loads((repo / "phase4" / "AMENDMENT_001_LOCK.json").read_text())
    req(a001["amendment_lock_sha256"] == A001_LOCK, "A001 lock mismatch")

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
    req(backend != "cpu", "Phase 5 S2 requires GPU/TPU JAX backend")

    from vascuquest.data import ArtifactAcquirer, DataPaths, SourceRegistry, verify_artifact
    from vascuquest.schema import load_manifest

    paths = DataPaths.default()
    vm = load_manifest()
    reg = SourceRegistry(paths.state_file("sources.json"))
    acq = ArtifactAcquirer(paths, reg, manifest=vm)
    report = {}
    for aid in ("model_variations", "common_site_waveforms_csv"):
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

    vq_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vq, text=True).strip()
    req(vq_commit == VQ_SHA, "VascuQuest commit mismatch")
    va_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = output_parent / f"locked_trial_phase5_s2_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "source_preflight.json").write_text(json.dumps(report, indent=2))

    cmd = [
        sys.executable,
        str(repo / "scripts" / "phase5_execute_s2.py"),
        "--execute-s2",
        "--expected-s2-lock-sha", S2_LOCK_SHA,
        "--repo-root", str(repo),
        "--pwdb-root", str(paths.source),
        "--phase4-evidence-root", str(phase4),
        "--output-root", str(out),
    ]
    print("Executing:", " ".join(shlex.quote(x) for x in cmd))

    started = time.time()
    proc = subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
    console = (proc.stdout or "") + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")
    (out / "phase5_console.log").write_text(console)
    print(console, end="" if console.endswith("\n") else "\n")
    req(proc.returncode == 0, f"Phase-5 S2 runner failed: {proc.returncode}")

    protocol = json.loads((repo / "phase5" / "S2_PROTOCOL.json").read_text())
    required = list(protocol["outputs"])
    missing = [name for name in required if not (out / name).exists()]
    req(not missing, f"missing Phase-5 S2 outputs: {missing}")

    summary = json.loads((out / "s2_summary.json").read_text())
    audit = json.loads((out / "s2_numerical_audit.json").read_text())
    p4check = json.loads((out / "phase4_evidence_verification.json").read_text())
    provenance = json.loads((out / "execution_provenance.json").read_text())

    req(summary["phase"] == 5 and summary["endpoint"] == "S2" and summary["status"] == "EXECUTED",
        "S2 summary state failure")
    req(summary["s2_lock_sha256"] == S2_LOCK_SHA, "S2 summary lock mismatch")
    req(summary["subjects"] == 4374 and summary["unordered_cross_age_pairs"] == 7971615,
        "S2 cardinality drift")
    req(summary["P0_alias_subjects"] == 2764, "S2 P0 subject gate failure")
    req(audit["status"] == "PASS", "S2 numerical audit failed")
    req(p4check["status"] == "PASS", "Phase-4 evidence verification failed")
    req(provenance["jax_backend"] != "cpu", "non-accelerated S2 execution")

    hashes = {name: h(out / name) for name in required}
    (out / "bundle_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True))

    evidence = {
        "phase": 5,
        "endpoint": "S2",
        "status": "EXECUTED",
        "s2_lock_sha256": S2_LOCK_SHA,
        "original_phase3_lock_sha256": ORIGINAL_PHASE3_LOCK,
        "amendment001_lock_sha256": A001_LOCK,
        "vascularage_execution_commit": va_commit,
        "vascuquest_commit": vq_commit,
        "jax_backend": backend,
        "jax_devices": devices,
        "phase4_reference_root": str(phase4),
        "output_root": str(out),
        "elapsed_seconds": time.time() - started,
        "bundle_hashes": hashes,
        "s2_summary": summary,
        "s2_numerical_audit": audit,
        "phase4_evidence_verification": p4check,
    }
    (out / "external_execution_evidence.json").write_text(json.dumps(evidence, indent=2))

    print("=" * 76)
    print("PHASE 5 S2 EXTERNAL EXECUTION: COMPLETE")
    print("=" * 76)
    print(json.dumps(summary, indent=2))
    print("Evidence bundle:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
