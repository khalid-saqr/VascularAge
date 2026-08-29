#!/usr/bin/env python3
"""Guarded Phase-5 execution of the prospectively deferred S2 robustness endpoint."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np

from vascularage.confirmatory import AGES
from vascularage.locked_io import duration_vector_from_counts, load_variations, load_waveform_matrix
from vascularage.phase5_s2 import (
    JACCARD_THRESHOLD,
    adjudicate_s2,
    age_pair_metrics_jax,
    jaccard_bool,
    matched_distance,
    selected_metrics_float64,
    subject_alias_exists,
)

ORIGINAL_PHASE3_LOCK = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
A001_LOCK = "1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7"


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fieldnames, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def load_s2_lock(repo: Path, expected_lock: str):
    manifest = json.loads((repo / "phase5" / "S2_LOCK.json").read_text())
    req(manifest["s2_lock_sha256"] == expected_lock, "unexpected Phase-5 S2 lock SHA")
    basis = manifest["canonical_basis"]
    computed = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    req(computed == expected_lock, "Phase-5 S2 canonical lock digest mismatch")
    req(basis["original_phase3_lock_sha256"] == ORIGINAL_PHASE3_LOCK, "Phase-3 lock identity drift")
    req(basis["amendment001_lock_sha256"] == A001_LOCK, "A001 lock identity drift")
    for rel, expected in basis["locked_files_sha256"].items():
        req(sha256(repo / rel) == expected, f"Phase-5 locked file drift: {rel}")
    return manifest


def validate_upstream_locks(repo: Path) -> None:
    p3 = json.loads((repo / "phase3" / "LOCK_MANIFEST.json").read_text())
    req(p3["lock_package_sha256"] == ORIGINAL_PHASE3_LOCK, "Phase-3 lock mismatch")
    a001 = json.loads((repo / "phase4" / "AMENDMENT_001_LOCK.json").read_text())
    req(a001["amendment_lock_sha256"] == A001_LOCK, "A001 lock mismatch")


def verify_phase4_evidence(phase4: Path, protocol: dict) -> dict:
    ref = protocol["phase4_reference"]
    req(phase4.name == ref["drive_folder"], "unexpected Phase-4 evidence directory")
    hashes = ref["artifact_sha256"]
    for name, expected in hashes.items():
        p = phase4 / name
        req(p.exists(), f"missing Phase-4 artifact: {name}")
        req(sha256(p) == expected, f"Phase-4 artifact drift: {name}")

    bundle_path = phase4 / "bundle_hashes.json"
    evidence_path = phase4 / "external_execution_evidence.json"
    summary_path = phase4 / "trial_summary.json"
    req(bundle_path.exists() and evidence_path.exists() and summary_path.exists(),
        "Phase-4 evidence metadata incomplete")

    bundle = json.loads(bundle_path.read_text())
    for name, expected in hashes.items():
        req(bundle.get(name) == expected, f"Phase-4 bundle hash mismatch: {name}")

    evidence = json.loads(evidence_path.read_text())
    summary = json.loads(summary_path.read_text())
    req(evidence["status"] == ref["status"], "Phase-4 external status mismatch")
    req(evidence["amendment_lock_sha256"] == A001_LOCK, "Phase-4 A001 evidence mismatch")
    req(evidence["original_phase3_lock_sha256"] == ORIGINAL_PHASE3_LOCK, "Phase-4 original lock mismatch")
    req(summary["P0_reproducibility_gate"] == "PASS", "Phase-4 P0 gate not PASS")
    req(summary["subjects"] == ref["subjects"], "Phase-4 subject cardinality mismatch")
    req(summary["unordered_cross_age_pairs"] == ref["unordered_cross_age_pairs"], "Phase-4 pair cardinality mismatch")
    req(summary["P0_reference_alias_pairs"] == ref["P0_reference_alias_pairs"], "Phase-4 P0 pair count mismatch")
    req(abs(summary["P0_reference_alias_fraction"] - ref["P0_reference_alias_fraction"]) < 1e-15,
        "Phase-4 P0 alias fraction mismatch")

    return {
        "status": "PASS",
        "phase4_root": str(phase4),
        "verified_artifact_sha256": hashes,
        "phase4_status": evidence["status"],
        "amendment001_lock_sha256": evidence["amendment_lock_sha256"],
        "original_phase3_lock_sha256": evidence["original_phase3_lock_sha256"],
        "P0_reproducibility_gate": summary["P0_reproducibility_gate"],
    }


def pair_indices_for_ages(ages: np.ndarray):
    for age_a, age_b in combinations(AGES, 2):
        ia = np.flatnonzero(ages == age_a).astype(np.int32)
        ib = np.flatnonzero(ages == age_b).astype(np.int32)
        req(ia.size == 729 and ib.size == 729, f"age block mismatch: {age_a},{age_b}")
        yield age_a, age_b, ia, ib


def compute_s2_components(waveforms: np.ndarray, ages: np.ndarray):
    ii, jj, l1, linf = [], [], [], []
    for age_a, age_b, ia, ib in pair_indices_for_ages(ages):
        print(f"S2 block {age_a} vs {age_b}", flush=True)
        b_l1, b_linf = age_pair_metrics_jax(waveforms, ia, ib)
        ii.append(np.repeat(ia, ib.size))
        jj.append(np.tile(ib, ia.size))
        l1.append(np.asarray(b_l1, dtype=np.float32).reshape(-1))
        linf.append(np.asarray(b_linf, dtype=np.float32).reshape(-1))
    return (
        np.concatenate(ii).astype(np.int32),
        np.concatenate(jj).astype(np.int32),
        np.concatenate(l1).astype(np.float32),
        np.concatenate(linf).astype(np.float32),
    )


def numerical_audit(waveforms, i, j, dt, l1, linf, d_l1, d_linf, protocol):
    tol = float(protocol["numerics"]["boundary_audit_abs_distance_to_one"])
    control_n = int(protocol["numerics"]["deterministic_control_pair_rows"])
    boundary = np.flatnonzero((np.abs(d_l1 - 1.0) <= tol) | (np.abs(d_linf - 1.0) <= tol))
    control = np.linspace(0, len(i) - 1, control_n, dtype=np.int64)
    sel = np.unique(np.concatenate([boundary.astype(np.int64), control]))
    ref_l1, ref_linf = selected_metrics_float64(waveforms, i[sel], j[sel])
    ref_d_l1 = matched_distance(ref_l1, dt[sel].astype(np.float64))
    ref_d_linf = matched_distance(ref_linf, dt[sel].astype(np.float64))
    prod_d_l1 = d_l1[sel].astype(np.float64)
    prod_d_linf = d_linf[sel].astype(np.float64)

    max_l1 = float(np.max(np.abs(ref_d_l1 - prod_d_l1))) if sel.size else 0.0
    max_linf = float(np.max(np.abs(ref_d_linf - prod_d_linf))) if sel.size else 0.0
    changed_l1 = int(np.sum((ref_d_l1 <= 1.0) != (prod_d_l1 <= 1.0)))
    changed_linf = int(np.sum((ref_d_linf <= 1.0) != (prod_d_linf <= 1.0)))
    allowed = float(protocol["numerics"]["max_abs_distance_disagreement"])
    req(max(max_l1, max_linf) <= allowed, "Phase-5 S2 float64 distance audit failed")
    req(changed_l1 == 0 and changed_linf == 0, "Phase-5 S2 float64 classification audit failed")

    return {
        "status": "PASS",
        "boundary_window_abs_distance_to_one": tol,
        "boundary_pair_rows": int(boundary.size),
        "deterministic_control_pair_rows_requested": control_n,
        "unique_pair_rows_audited": int(sel.size),
        "max_abs_distance_difference_L1": max_l1,
        "max_abs_distance_difference_Linf": max_linf,
        "classification_changes_L1": changed_l1,
        "classification_changes_Linf": changed_linf,
        "maximum_allowed_distance_difference": allowed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute-s2", action="store_true")
    ap.add_argument("--expected-s2-lock-sha", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--pwdb-root", required=True)
    ap.add_argument("--phase4-evidence-root", required=True)
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()

    req(args.execute_s2, "Phase-5 S2 biological execution requires --execute-s2")
    repo = Path(args.repo_root).resolve()
    pwdb = Path(args.pwdb_root).resolve()
    phase4 = Path(args.phase4_evidence_root).resolve()
    out = Path(args.output_root).resolve()
    out.mkdir(parents=True, exist_ok=True)

    try:
        manifest = load_s2_lock(repo, args.expected_s2_lock_sha)
        validate_upstream_locks(repo)
        protocol = json.loads((repo / "phase5" / "S2_PROTOCOL.json").read_text())
        req(protocol["status"] == "PROSPECTIVELY_LOCKED_NOT_EXECUTED", "Phase-5 protocol status drift")

        p4check = verify_phase4_evidence(phase4, protocol)
        (out / "phase4_evidence_verification.json").write_text(json.dumps(p4check, indent=2))

        import jax
        req(jax.default_backend() != "cpu", "Phase-5 S2 execution requires non-CPU JAX backend")

        ages, _ = load_variations(pwdb / "pwdb_model_variations.csv")
        radial, counts = load_waveform_matrix(pwdb / "PWs_csv.zip", "Radial", "P")
        durations = duration_vector_from_counts(counts)

        p0 = np.load(phase4 / "primary_pair_components.npz")
        req(set(p0.files) == {"i", "j", "pressure_rmse_mmHg", "duration_diff_ms"}, "Phase-4 P0 pair schema drift")
        p0_i = p0["i"].astype(np.int32, copy=False)
        p0_j = p0["j"].astype(np.int32, copy=False)
        p0_dt = p0["duration_diff_ms"].astype(np.float32, copy=False)
        p0_dp = p0["pressure_rmse_mmHg"].astype(np.float32, copy=False)
        req(len(p0_i) == protocol["phase4_reference"]["unordered_cross_age_pairs"], "P0 pair cardinality drift")

        i, j, l1, linf = compute_s2_components(radial, ages)
        req(np.array_equal(i, p0_i) and np.array_equal(j, p0_j), "S2 pair ordering differs from preserved P0")

        dt_recomputed = np.abs(durations[i] - durations[j]).astype(np.float32)
        req(np.array_equal(dt_recomputed, p0_dt), "S2 recomputed duration differs from preserved P0")
        dt = p0_dt

        d_p0 = matched_distance(p0_dp, dt)
        d_l1 = matched_distance(l1, dt)
        d_linf = matched_distance(linf, dt)
        p0_pair_alias = d_p0 <= 1.0
        l1_pair_alias = d_l1 <= 1.0
        linf_pair_alias = d_linf <= 1.0

        A_p0 = subject_alias_exists(i, j, p0_pair_alias)
        A_l1 = subject_alias_exists(i, j, l1_pair_alias)
        A_linf = subject_alias_exists(i, j, linf_pair_alias)

        ref = protocol["phase4_reference"]
        req(int(p0_pair_alias.sum()) == ref["P0_reference_alias_pairs"], "P0 pair alias count changed in Phase 5")
        req(int(A_p0.sum()) == ref["P0_reference_alias_subjects"], "P0 subject alias count changed in Phase 5")

        j_l1 = jaccard_bool(A_l1, A_p0)
        j_linf = jaccard_bool(A_linf, A_p0)
        s2_no_go = adjudicate_s2(j_l1, j_linf, float(protocol["jaccard_threshold"]))

        np.savez_compressed(
            out / "s2_pair_components.npz",
            i=i,
            j=j,
            duration_diff_ms=dt,
            l1_pressure_mmHg=l1,
            linf_pressure_mmHg=linf,
        )

        rows = [
            {
                "subject_id": k + 1,
                "age": int(ages[k]),
                "P0_alias": bool(A_p0[k]),
                "L1_alias": bool(A_l1[k]),
                "Linf_alias": bool(A_linf[k]),
            }
            for k in range(len(ages))
        ]
        write_csv(out / "s2_subject_results.csv", list(rows[0]), rows)

        overlap = {
            "P0_alias_subjects": int(A_p0.sum()),
            "L1_alias_subjects": int(A_l1.sum()),
            "Linf_alias_subjects": int(A_linf.sum()),
            "L1_intersection_with_P0": int(np.logical_and(A_l1, A_p0).sum()),
            "L1_union_with_P0": int(np.logical_or(A_l1, A_p0).sum()),
            "Linf_intersection_with_P0": int(np.logical_and(A_linf, A_p0).sum()),
            "Linf_union_with_P0": int(np.logical_or(A_linf, A_p0).sum()),
            "Jaccard_L1_vs_P0": j_l1,
            "Jaccard_Linf_vs_P0": j_linf,
        }
        (out / "s2_overlap_summary.json").write_text(json.dumps(overlap, indent=2))

        audit = numerical_audit(radial, i, j, dt, l1, linf, d_l1, d_linf, protocol)
        (out / "s2_numerical_audit.json").write_text(json.dumps(audit, indent=2))

        summary = {
            "phase": 5,
            "endpoint": "S2",
            "status": "EXECUTED",
            "s2_lock_sha256": args.expected_s2_lock_sha,
            "subjects": 4374,
            "unordered_cross_age_pairs": 7971615,
            "pressure_scale_mmHg": 5.0,
            "duration_scale_ms": 10.0,
            "P0_alias_subjects": int(A_p0.sum()),
            "L1_alias_subjects": int(A_l1.sum()),
            "Linf_alias_subjects": int(A_linf.sum()),
            "Jaccard_L1_vs_P0": j_l1,
            "Jaccard_Linf_vs_P0": j_linf,
            "S2_threshold": JACCARD_THRESHOLD,
            "S2_NO_GO": s2_no_go,
            "S2_adjudication": "NO_GO_ROBUST_ALIASING_CLAIM" if s2_no_go else "PASS",
            "numerical_audit": audit["status"],
            "phase4_evidence_verification": p4check["status"],
        }
        (out / "s2_summary.json").write_text(json.dumps(summary, indent=2))

        repo_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        provenance = {
            "phase": 5,
            "endpoint": "S2",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "vascularage_commit": repo_commit,
            "s2_lock_manifest": manifest,
            "phase4_evidence_root": str(phase4),
            "jax_backend": jax.default_backend(),
            "jax_devices": [str(d) for d in jax.devices()],
            "numpy_version": np.__version__,
            "jax_version": jax.__version__,
        }
        (out / "execution_provenance.json").write_text(json.dumps(provenance, indent=2))
        print("=" * 76)
        print("PHASE 5 S2 ROBUSTNESS: EXECUTED")
        print("=" * 76)
        print(json.dumps(summary, indent=2))
        return 0

    except Exception as exc:
        (out / "execution_failure.json").write_text(json.dumps({
            "phase": 5,
            "endpoint": "S2",
            "status": "FAILED",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "files_present": sorted(p.name for p in out.iterdir()),
        }, indent=2))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
