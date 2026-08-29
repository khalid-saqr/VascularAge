#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_SHA = "97d831b3b3770dddcec9101f3095ecd92d190c4c9f4a1c17e67c2a6c3b8dfb05"
NOTEBOOK_SOURCE_SHA256 = "223414d4477a707eb9aab0e24bd2c947cabc2c10658ab1e0d5facc7a86805b50"
ORIGINAL_PHASE3_LOCK = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
A001_LOCK = "1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7"
NOTEBOOK = ROOT / "notebooks" / "05_s2_robustness.ipynb"


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
    manifest = json.loads((ROOT / "phase5" / "S2_LOCK.json").read_text())
    req(manifest["s2_lock_sha256"] == LOCK_SHA, "Phase-5 S2 lock identity mismatch")
    basis = manifest["canonical_basis"]
    computed = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    req(computed == LOCK_SHA, "Phase-5 S2 canonical digest mismatch")
    req(basis["original_phase3_lock_sha256"] == ORIGINAL_PHASE3_LOCK, "Phase-3 lock identity drift")
    req(basis["amendment001_lock_sha256"] == A001_LOCK, "A001 lock identity drift")
    for rel, expected in basis["locked_files_sha256"].items():
        req(h(ROOT / rel) == expected, f"Phase-5 locked file drift: {rel}")

    p3 = json.loads((ROOT / "phase3" / "LOCK_MANIFEST.json").read_text())
    a001 = json.loads((ROOT / "phase4" / "AMENDMENT_001_LOCK.json").read_text())
    req(p3["lock_package_sha256"] == ORIGINAL_PHASE3_LOCK, "original Phase-3 lock changed")
    req(a001["amendment_lock_sha256"] == A001_LOCK, "A001 lock changed")

    protocol = json.loads((ROOT / "phase5" / "S2_PROTOCOL.json").read_text())
    req(protocol["phase"] == 5 and protocol["endpoint"] == "S2", "S2 protocol identity drift")
    req(protocol["status"] == "PROSPECTIVELY_LOCKED_NOT_EXECUTED", "S2 protocol status drift")
    req(protocol["matched_scales"] == {"duration_ms": 10.0, "pressure_mmHg": 5.0}, "matched scales changed")
    req(protocol["jaccard_threshold"] == 0.5, "S2 threshold changed")
    req(protocol["metrics"]["L1_pressure"]["definition"] == "mean(abs(P_i-P_j)) over 512 phase points",
        "L1 metric definition changed")
    req(protocol["metrics"]["L1_pressure"]["raw_unnormalised_sum_forbidden"] is True,
        "raw L1 sum prohibition removed")
    req(protocol["metrics"]["Linf_pressure"]["definition"] == "max(abs(P_i-P_j)) over 512 phase points",
        "Linf metric definition changed")
    req(protocol["S2_NO_GO"] == "Jaccard(A_L1,A_P0) < 0.50 AND Jaccard(A_Linf,A_P0) < 0.50",
        "S2 Boolean rule changed")
    ref = protocol["phase4_reference"]
    req(ref["drive_folder"] == "locked_trial_amendment001_20260829T153743Z", "Phase-4 evidence root changed")
    req(ref["P0_reference_alias_subjects"] == 2764, "P0 subject reference changed")
    req(ref["P0_reference_alias_pairs"] == 53842, "P0 pair reference changed")
    req(ref["unordered_cross_age_pairs"] == 7971615, "pair universe changed")

    primitives = (ROOT / "src" / "vascularage" / "phase5_s2.py").read_text()
    for token in (
        "np.mean(np.abs(x - y))",
        "np.max(np.abs(x - y))",
        "j_l1 < threshold and j_linf < threshold",
        "jnp.mean(diff, axis=2)",
        "jnp.max(diff, axis=2)",
    ):
        req(token in primitives, f"S2 primitive missing: {token}")

    runner = (ROOT / "scripts" / "phase5_execute_s2.py").read_text()
    for token in (
        "--execute-s2",
        "verify_phase4_evidence",
        "np.array_equal(i, p0_i)",
        "np.array_equal(j, p0_j)",
        "np.array_equal(dt_recomputed, p0_dt)",
        "P0_reference_alias_subjects",
        "numerical_audit",
        "adjudicate_s2",
        "execution_failure.json",
    ):
        req(token in runner, f"S2 runner guard missing: {token}")

    wrapper = (ROOT / "scripts" / "phase5_colab.py").read_text()
    for token in (
        LOCK_SHA,
        "--phase4-root",
        "--output-parent",
        "PHASE 5 S2 EXTERNAL EXECUTION: COMPLETE",
        "jax.default_backend()",
    ):
        req(token in wrapper, f"Colab wrapper token missing: {token}")

    nb = json.loads(NOTEBOOK.read_text())
    req(nb["nbformat"] == 4, "Phase-5 notebook format drift")
    sig = source_signature(nb)
    req(sig == NOTEBOOK_SOURCE_SHA256, "Phase-5 notebook source cells changed")
    all_source = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    for token in (
        LOCK_SHA,
        "phase-05-s2-robustness",
        "phase5_colab.py",
        "--execute-s2",
        "locked_trial_amendment001_20260829T153743Z",
        "/content/drive/MyDrive/VascularAge/phase_05",
    ):
        req(token in all_source, f"Phase-5 notebook token missing: {token}")

    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    executed = any(c.get("execution_count") is not None or c.get("outputs") for c in code)
    if not executed:
        for c in code:
            req(c.get("execution_count") is None, "pre-execution notebook execution count drift")
            req(c.get("outputs") == [], "pre-execution notebook contains output")
        state = "PRE_EXECUTION_LOCKED"
    else:
        text = output_text(nb)
        success = (
            "PHASE 5 S2 EXTERNAL EXECUTION: COMPLETE" in text
            and "PHASE 5 S2 NOTEBOOK: SUCCESS" in text
        )
        failed = (
            "CalledProcessError" in text
            or "Phase-5 S2 runner failed" in text
            or "execution_failure.json" in text
        )
        req(success or failed, "executed Phase-5 notebook lacks terminal success/failure evidence")
        req(not (success and failed), "Phase-5 notebook contains conflicting terminal states")
        state = "POST_EXECUTION_SUCCESS" if success else "POST_EXECUTION_FAILED"

    print("Phase 5 S2 static validation: PASS")
    print("S2 lock:", LOCK_SHA)
    print("Notebook source signature:", sig)
    print("Notebook state:", state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
