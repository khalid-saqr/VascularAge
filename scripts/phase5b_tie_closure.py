#!/usr/bin/env python3
"""Execute the Phase-5B compensation tie-sensitivity closure.

This is an evidence-only closure. It reads preserved Phase-4 artifacts, reconstructs
co-nearest sets under the locked 1e-6 tolerance, and never reads PWDB waveforms or
VascuQuest data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from vascularage.phase5b_ties import (
    FACTOR_ORDER,
    N_CROSS_AGE_PAIRS,
    N_SUBJECTS,
    TIE_ATOL,
    bool_from_csv,
    reconstruct_nearest_from_pairs,
    reference_distance_float32,
    validate_canonical_compensation_rows,
)


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_lock(repo: Path, expected_lock_sha: str) -> tuple[dict, dict]:
    manifest = json.loads((repo / "phase5b" / "TIE_SENSITIVITY_LOCK.json").read_text())
    req(manifest["tie_sensitivity_lock_sha256"] == expected_lock_sha, "Phase-5B lock identity mismatch")
    basis = manifest["canonical_basis"]
    computed = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    req(computed == expected_lock_sha, "Phase-5B canonical lock digest mismatch")
    for rel, expected in basis["locked_files_sha256"].items():
        req(sha256(repo / rel) == expected, f"Phase-5B locked file drift: {rel}")

    spec = json.loads((repo / "phase5b" / "TIE_SENSITIVITY_SPEC.json").read_text())
    req(spec["status"] == "PROSPECTIVELY_LOCKED_NOT_EXECUTED", "Phase-5B spec state drift")
    req(spec["tie_definition"]["tie_atol"] == TIE_ATOL, "tie tolerance drift")
    req(spec["closure_rule"]["no_new_randomness"] is True, "randomness prohibition removed")
    req(spec["closure_rule"]["no_waveform_or_PWDB_access"] is True, "PWDB prohibition removed")

    p3 = json.loads((repo / "phase3" / "LOCK_MANIFEST.json").read_text())
    a001 = json.loads((repo / "phase4" / "AMENDMENT_001_LOCK.json").read_text())
    s2 = json.loads((repo / "phase5" / "S2_LOCK.json").read_text())
    req(p3["lock_package_sha256"] == spec["original_phase3_lock_sha256"], "Phase-3 lock mismatch")
    req(a001["amendment_lock_sha256"] == spec["amendment001_lock_sha256"], "A001 lock mismatch")
    req(s2["s2_lock_sha256"] == spec["phase5_s2_lock_sha256"], "Phase-5 S2 lock mismatch")
    return manifest, spec


def verify_phase4_evidence(phase4: Path, spec: dict) -> dict:
    ref = spec["phase4_reference"]
    req(phase4.is_dir(), f"Phase-4 evidence directory missing: {phase4}")
    req(phase4.name == ref["drive_folder"], "Phase-4 evidence folder identity mismatch")
    observed = {}
    for name, expected in ref["required_artifact_sha256"].items():
        path = phase4 / name
        req(path.is_file(), f"missing preserved Phase-4 artifact: {name}")
        observed[name] = sha256(path)
        req(observed[name] == expected, f"Phase-4 artifact hash mismatch: {name}")
    return {
        "status": "PASS",
        "phase4_root": str(phase4),
        "verified_artifact_sha256": observed,
        "original_phase3_lock_sha256": spec["original_phase3_lock_sha256"],
        "amendment001_lock_sha256": spec["amendment001_lock_sha256"],
    }


def verify_motif_table(path: Path, expected_total: int, expected_top20_count: int) -> dict:
    rows = read_csv(path)
    req(rows, "compensation_motifs.csv is empty")
    counts = [int(row["count"]) for row in rows]
    req(sum(counts) == expected_total, "motif table count total mismatch")
    req(sum(sorted(counts, reverse=True)[:20]) == expected_top20_count, "motif table top-20 count mismatch")
    return {
        "motif_rows": len(rows),
        "count_total": sum(counts),
        "top20_count": sum(sorted(counts, reverse=True)[:20]),
        "status": "PASS",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute-tie-closure", action="store_true")
    ap.add_argument("--expected-lock-sha", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--phase4-evidence-root", required=True)
    ap.add_argument("--output-parent", required=True)
    args = ap.parse_args()

    req(args.execute_tie_closure, "Phase-5B tie-sensitivity execution requires --execute-tie-closure")

    repo = Path(args.repo_root).resolve()
    phase4 = Path(args.phase4_evidence_root).resolve()
    output_parent = Path(args.output_parent).resolve()

    manifest, spec = validate_lock(repo, args.expected_lock_sha)
    p4check = verify_phase4_evidence(phase4, spec)

    started = time.time()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = output_parent / f"locked_trial_phase5b_tie_closure_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "phase4_evidence_verification.json").write_text(json.dumps(p4check, indent=2, sort_keys=True))

    pair_path = phase4 / "primary_pair_components.npz"
    with np.load(pair_path) as data:
        for key in ("i", "j", "pressure_rmse_mmHg", "duration_diff_ms"):
            req(key in data.files, f"primary pair artifact missing array: {key}")
        i = np.asarray(data["i"], dtype=np.int32)
        j = np.asarray(data["j"], dtype=np.int32)
        dp = np.asarray(data["pressure_rmse_mmHg"], dtype=np.float32)
        dt = np.asarray(data["duration_diff_ms"], dtype=np.float32)

    req(len(i) == N_CROSS_AGE_PAIRS, "cross-age pair count drift")
    req(i.shape == j.shape == dp.shape == dt.shape, "pair-component array shape drift")

    dref = reference_distance_float32(dp, dt)
    nearest = reconstruct_nearest_from_pairs(N_SUBJECTS, i, j, dref, tie_atol=TIE_ATOL)

    subject_rows = read_csv(phase4 / "primary_subject_results.csv")
    req(len(subject_rows) == N_SUBJECTS, "subject table cardinality drift")
    subject_rows = sorted(subject_rows, key=lambda row: int(row["subject_id"]))
    req([int(row["subject_id"]) for row in subject_rows] == list(range(1, N_SUBJECTS + 1)),
        "subject IDs are not canonical 1..4374")

    recorded_best = np.array([float(row["D_ref"]) for row in subject_rows], dtype=np.float64)
    recorded_target = np.array([int(row["nearest_subject_id"]) - 1 for row in subject_rows], dtype=np.int32)
    recorded_ties = np.array([int(row["tie_count"]) for row in subject_rows], dtype=np.int32)
    recorded_alias = np.array([bool_from_csv(row["reference_alias"]) for row in subject_rows], dtype=bool)

    best_abs_diff = np.abs(nearest.best_distance.astype(np.float64) - recorded_best)
    req(float(best_abs_diff.max()) <= 1e-7, "reconstructed nearest distance disagrees with Phase-4 subject table")
    req(np.array_equal(nearest.canonical_target, recorded_target), "reconstructed canonical targets disagree")
    req(np.array_equal(nearest.co_nearest_count, recorded_ties), "reconstructed tie counts disagree")
    req(np.array_equal(nearest.best_distance <= np.float32(1.0), recorded_alias),
        "reconstructed P0 alias classes disagree")

    alias_count = int(recorded_alias.sum())
    req(alias_count == spec["phase4_reference"]["expected_P0_alias_subjects"], "P0 alias subject count drift")

    global_tied = nearest.co_nearest_count > 1
    alias_tied = global_tied & recorded_alias
    global_tied_count = int(global_tied.sum())
    alias_tied_count = int(alias_tied.sum())
    max_count_all = int(nearest.co_nearest_count.max())
    max_count_alias = int(nearest.co_nearest_count[recorded_alias].max())
    min_gap_all = float(nearest.second_nearest_gap.min())
    min_gap_alias = float(nearest.second_nearest_gap[recorded_alias].min())

    audit_rows = []
    for idx, row in enumerate(subject_rows):
        audit_rows.append({
            "subject_id": idx + 1,
            "age": int(row["age"]),
            "reference_alias": bool(recorded_alias[idx]),
            "best_distance_reconstructed": float(nearest.best_distance[idx]),
            "canonical_target_subject_id": int(nearest.canonical_target[idx]) + 1,
            "co_nearest_count": int(nearest.co_nearest_count[idx]),
            "second_nearest_gap": float(nearest.second_nearest_gap[idx]),
        })
    write_csv(
        out / "tie_subject_audit.csv",
        [
            "subject_id", "age", "reference_alias", "best_distance_reconstructed",
            "canonical_target_subject_id", "co_nearest_count", "second_nearest_gap",
        ],
        audit_rows,
    )

    compensation_rows = read_csv(phase4 / "compensation_vectors.csv")
    comp = validate_canonical_compensation_rows(subject_rows, compensation_rows)
    req(comp["P0_alias_sources"] == alias_count, "compensation source cardinality drift")

    null_summary = json.loads((phase4 / "compensation_null_summary.json").read_text())
    expected = spec["phase4_reference"]
    req(abs(float(null_summary["top20_observed"]) - expected["expected_canonical_top20_motif_concentration"]) <= 1e-15,
        "canonical top-20 concentration drift")
    req(abs(comp["top20_motif_concentration_recomputed"] - float(null_summary["top20_observed"])) <= 1e-15,
        "canonical top-20 concentration failed independent recomputation")
    req(abs(float(null_summary["null_95th"]) - expected["expected_null_95th"]) <= 1e-15,
        "locked null 95th percentile drift")
    req(int(null_summary["permutations"]) == expected["expected_null_permutations"], "null permutation count drift")
    req(bool(null_summary["S4_no_go"]) is expected["expected_S4_no_go"], "canonical S4 state drift")

    motif_table = verify_motif_table(
        phase4 / "compensation_motifs.csv",
        expected_total=comp["vector_count"],
        expected_top20_count=comp["top20_count"],
    )

    canonical_check = {
        **comp,
        "motif_table_verification": motif_table,
        "canonical_top20_from_phase4": float(null_summary["top20_observed"]),
        "locked_null_95th": float(null_summary["null_95th"]),
        "locked_null_permutations": int(null_summary["permutations"]),
        "canonical_S4_no_go": bool(null_summary["S4_no_go"]),
        "status": "PASS",
    }
    (out / "canonical_compensation_verification.json").write_text(
        json.dumps(canonical_check, indent=2, sort_keys=True)
    )

    stop = alias_tied_count > 0
    if stop:
        outcome = "CO_NEAREST_ALTERNATIVES_PRESENT_STOP"
        closure = "STOP"
        co_nearest_top20 = None
        difference = None
    else:
        outcome = "NO_CO_NEAREST_ALTERNATIVES"
        closure = "PASS"
        co_nearest_top20 = float(null_summary["top20_observed"])
        difference = 0.0

    summary = {
        "phase": "5B",
        "endpoint": "COMPENSATION_TIE_SENSITIVITY_CLOSURE",
        "status": "EXECUTED" if not stop else "STOPPED",
        "tie_sensitivity_lock_sha256": args.expected_lock_sha,
        "subjects": N_SUBJECTS,
        "unordered_cross_age_pairs": N_CROSS_AGE_PAIRS,
        "P0_alias_sources": alias_count,
        "tie_atol": TIE_ATOL,
        "subjects_with_co_nearest_alternatives_all": global_tied_count,
        "P0_alias_sources_with_co_nearest_alternatives": alias_tied_count,
        "maximum_co_nearest_count_all": max_count_all,
        "maximum_co_nearest_count_P0_alias": max_count_alias,
        "minimum_nearest_second_gap_all": min_gap_all,
        "minimum_nearest_second_gap_P0_alias": min_gap_alias,
        "canonical_top20_motif_concentration": float(null_summary["top20_observed"]),
        "co_nearest_sensitive_top20_motif_concentration": co_nearest_top20,
        "top20_difference": difference,
        "locked_null_95th": float(null_summary["null_95th"]),
        "S4_reopened": False,
        "new_null_distribution_generated": False,
        "randomness_used": False,
        "waveform_or_PWDB_accessed": False,
        "outcome": outcome,
        "closure_adjudication": closure,
    }
    (out / "tie_sensitivity_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))

    try:
        repo_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
    except Exception:
        repo_commit = None
    provenance = {
        "phase": "5B",
        "endpoint": "COMPENSATION_TIE_SENSITIVITY_CLOSURE",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "vascularage_commit": repo_commit,
        "tie_sensitivity_lock_sha256": args.expected_lock_sha,
        "parent_main_commit": spec["parent_main_commit"],
        "phase4_evidence_root": str(phase4),
        "output_root": str(out),
        "numpy_version": np.__version__,
        "python_version": sys.version,
        "execution_class": "evidence_only_cpu",
        "elapsed_seconds": time.time() - started,
    }
    (out / "execution_provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True))

    required = list(spec["outputs"])
    missing = [name for name in required if not (out / name).is_file()]
    req(not missing, f"missing Phase-5B outputs: {missing}")
    hashes = {name: sha256(out / name) for name in required}
    (out / "bundle_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True))

    external = {
        "phase": "5B",
        "endpoint": "COMPENSATION_TIE_SENSITIVITY_CLOSURE",
        "status": summary["status"],
        "tie_sensitivity_lock_sha256": args.expected_lock_sha,
        "vascularage_execution_commit": repo_commit,
        "phase4_reference_root": str(phase4),
        "output_root": str(out),
        "bundle_hashes": hashes,
        "tie_sensitivity_summary": summary,
        "phase4_evidence_verification": p4check,
        "canonical_compensation_verification": canonical_check,
    }
    (out / "external_execution_evidence.json").write_text(json.dumps(external, indent=2, sort_keys=True))

    print("=" * 76)
    print("PHASE 5B TIE-SENSITIVITY CLOSURE:", closure)
    print("=" * 76)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("Evidence bundle:", out)
    if stop:
        print("PHASE 5B CLOSURE: STOP")
        print("No co-nearest aggregation rule was invented or applied.")
        return 2
    print("PHASE 5B CLOSURE: COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
