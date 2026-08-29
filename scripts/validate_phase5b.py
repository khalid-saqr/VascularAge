#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_SHA = "6b9f11bf0c662c8263e531b0440882881d79b5ab70aaa4aaeffd4e4a69d741c2"
NOTEBOOK_SOURCE_SHA256 = "363440e54215cdd473124cebac7c6114fc1ed1074615999a3ebd2637c6bfc9c6"
ORIGINAL_PHASE3_LOCK = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
A001_LOCK = "1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7"
S2_LOCK = "97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05"
PARENT_MAIN = "dd64cf00699ade42ba4505ddc6f0ffa20a982894"
PHASE4_REFERENCE = "locked_trial_amendment001_20260829T153743Z"
NOTEBOOK = ROOT / "notebooks" / "06_tie_sensitivity_closure.ipynb"


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_signature(nb: dict) -> str:
    basis = [
        {"cell_type": c["cell_type"], "source": c.get("source", [])}
        for c in nb["cells"]
    ]
    return hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def output_text(nb: dict) -> str:
    parts = []
    for cell in nb["cells"]:
        for out in cell.get("outputs", []):
            text = out.get("text", [])
            parts.extend([text] if isinstance(text, str) else text)
            parts.append(out.get("evalue", ""))
            parts.extend(out.get("traceback", []))
            plain = out.get("data", {}).get("text/plain", [])
            parts.extend([plain] if isinstance(plain, str) else plain)
    return "\n".join(parts)


def main() -> int:
    manifest = json.loads((ROOT / "phase5b" / "TIE_SENSITIVITY_LOCK.json").read_text())
    req(manifest["tie_sensitivity_lock_sha256"] == LOCK_SHA, "Phase-5B lock identity mismatch")
    basis = manifest["canonical_basis"]
    computed = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    req(computed == LOCK_SHA, "Phase-5B canonical digest mismatch")
    req(basis["parent_main_commit"] == PARENT_MAIN, "Phase-5B parent main drift")
    req(basis["original_phase3_lock_sha256"] == ORIGINAL_PHASE3_LOCK, "Phase-3 lock identity drift")
    req(basis["amendment001_lock_sha256"] == A001_LOCK, "A001 lock identity drift")
    req(basis["phase5_s2_lock_sha256"] == S2_LOCK, "Phase-5 S2 lock identity drift")
    req(basis["phase4_reference_drive_folder"] == PHASE4_REFERENCE, "Phase-4 reference folder drift")
    for rel, expected in basis["locked_files_sha256"].items():
        req(h(ROOT / rel) == expected, f"Phase-5B locked file drift: {rel}")

    p3 = json.loads((ROOT / "phase3" / "LOCK_MANIFEST.json").read_text())
    a001 = json.loads((ROOT / "phase4" / "AMENDMENT_001_LOCK.json").read_text())
    s2 = json.loads((ROOT / "phase5" / "S2_LOCK.json").read_text())
    req(p3["lock_package_sha256"] == ORIGINAL_PHASE3_LOCK, "original Phase-3 lock changed")
    req(a001["amendment_lock_sha256"] == A001_LOCK, "A001 lock changed")
    req(s2["s2_lock_sha256"] == S2_LOCK, "Phase-5 S2 lock changed")

    spec = json.loads((ROOT / "phase5b" / "TIE_SENSITIVITY_SPEC.json").read_text())
    req(spec["phase"] == "5B" and spec["endpoint"] == "COMPENSATION_TIE_SENSITIVITY_CLOSURE",
        "Phase-5B spec identity drift")
    req(spec["status"] == "PROSPECTIVELY_LOCKED_NOT_EXECUTED", "Phase-5B spec status drift")
    req(spec["parent_main_commit"] == PARENT_MAIN, "Phase-5B parent commit drift")
    req(spec["tie_definition"]["tie_atol"] == 1e-6, "tie tolerance changed")
    req(spec["phase4_reference"]["drive_folder"] == PHASE4_REFERENCE, "Phase-4 evidence root changed")
    req(spec["phase4_reference"]["expected_subjects"] == 4374, "subject cardinality changed")
    req(spec["phase4_reference"]["expected_unordered_cross_age_pairs"] == 7971615, "pair universe changed")
    req(spec["phase4_reference"]["expected_P0_alias_subjects"] == 2764, "P0 alias source count changed")
    req(spec["closure_rule"]["no_new_S4_adjudication"] is True, "S4 reopening prohibition removed")
    req(spec["closure_rule"]["no_new_null_distribution"] is True, "new-null prohibition removed")
    req(spec["closure_rule"]["no_new_randomness"] is True, "randomness prohibition removed")
    req(spec["closure_rule"]["no_waveform_or_PWDB_access"] is True, "PWDB prohibition removed")
    req(spec["closure_rule"]["no_VascuQuest_dependency"] is True, "VascuQuest prohibition removed")
    req(spec["closure_rule"]["no_GPU_requirement"] is True, "CPU-only closure contract changed")
    for name, expected in basis["phase4_reference_artifact_sha256"].items():
        req(spec["phase4_reference"]["required_artifact_sha256"][name] == expected,
            f"Phase-4 artifact binding drift: {name}")

    primitives = (ROOT / "src" / "vascularage" / "phase5b_ties.py").read_text()
    for token in (
        "TIE_ATOL = 1e-6",
        "reference_distance_float32",
        "reconstruct_nearest_from_pairs",
        "dd <= (best[ii] + np.float32(tie_atol))",
        "top_k_motif_concentration",
    ):
        req(token in primitives, f"Phase-5B primitive missing: {token}")

    runner = (ROOT / "scripts" / "phase5b_tie_closure.py").read_text()
    for token in (
        "--execute-tie-closure",
        "verify_phase4_evidence",
        "primary_pair_components.npz",
        "primary_subject_results.csv",
        "compensation_vectors.csv",
        "compensation_motifs.csv",
        "compensation_null_summary.json",
        "alias_tied_count > 0",
        "CO_NEAREST_ALTERNATIVES_PRESENT_STOP",
        "NO_CO_NEAREST_ALTERNATIVES",
        "PHASE 5B CLOSURE: COMPLETE",
    ):
        req(token in runner, f"Phase-5B runner guard missing: {token}")
    for forbidden in (
        "from vascuquest",
        "import vascuquest",
        "load_waveform_matrix",
        "PWs_csv",
        "np.random",
        "import jax",
    ):
        req(forbidden not in runner, f"Phase-5B runner contains prohibited dependency/operation: {forbidden}")

    nb = json.loads(NOTEBOOK.read_text())
    req(nb["nbformat"] == 4, "Phase-5B notebook format drift")
    sig = source_signature(nb)
    req(sig == NOTEBOOK_SOURCE_SHA256, "Phase-5B notebook source cells changed")
    all_source = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    for token in (
        LOCK_SHA,
        "phase-05b-tie-sensitivity-closure",
        "phase5b_tie_closure.py",
        "--execute-tie-closure",
        PHASE4_REFERENCE,
        "/content/drive/MyDrive/VascularAge/phase_05b",
    ):
        req(token in all_source, f"Phase-5B notebook token missing: {token}")
    for forbidden in ("VascuQuest.git", "PWs_csv.zip", "jax.default_backend()", "accelerator"):
        req(forbidden not in all_source, f"Phase-5B notebook contains prohibited execution dependency: {forbidden}")

    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    executed = any(c.get("execution_count") is not None or c.get("outputs") for c in code)
    if not executed:
        for cell in code:
            req(cell.get("execution_count") is None, "pre-execution notebook execution count drift")
            req(cell.get("outputs") == [], "pre-execution notebook contains output")
        state = "PRE_EXECUTION_LOCKED"
    else:
        text = output_text(nb)
        success = (
            "PHASE 5B TIE-SENSITIVITY CLOSURE: PASS" in text
            and "PHASE 5B CLOSURE: COMPLETE" in text
            and "PHASE 5B NOTEBOOK: SUCCESS" in text
        )
        stopped = (
            "PHASE 5B CLOSURE: STOP" in text
            or "CalledProcessError" in text
        )
        req(success or stopped, "executed Phase-5B notebook lacks terminal success/stop evidence")
        req(not (success and stopped), "Phase-5B notebook contains conflicting terminal states")
        state = "POST_EXECUTION_SUCCESS" if success else "POST_EXECUTION_STOP"

    print("Phase 5B tie-sensitivity static validation: PASS")
    print("Tie-sensitivity lock:", LOCK_SHA)
    print("Notebook source signature:", sig)
    print("Notebook state:", state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
