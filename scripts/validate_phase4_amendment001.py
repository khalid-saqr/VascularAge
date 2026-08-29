#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILED_NB = ROOT / "notebooks" / "04_confirmatory_trial.ipynb"
AMENDED_NB = ROOT / "notebooks" / "04_confirmatory_trial_amendment001.ipynb"
LOCK = ROOT / "phase4" / "AMENDMENT_001_LOCK.json"
ORIGINAL_LOCK_SHA = "89321ec7c7c8909814cd8ab121726c0fcdf0ce5ec2bc44f67795759690b66963"
AMENDMENT_LOCK_SHA = "1a87a71b638ae4311a1fc4d71c07b4a4a7760f0087a8a25f534774c36bccf7d7"


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook_text(nb: dict) -> str:
    parts = []
    for cell in nb["cells"]:
        parts.extend(cell.get("source", []))
        for output in cell.get("outputs", []):
            parts.extend(output.get("text", []))
            parts.append(output.get("evalue", ""))
            parts.extend(output.get("traceback", []))
    return "\n".join(parts)


def notebook_output_text(nb: dict) -> str:
    parts = []
    for cell in nb["cells"]:
        for output in cell.get("outputs", []):
            parts.extend(output.get("text", []))
            parts.append(output.get("evalue", ""))
            parts.extend(output.get("traceback", []))
    return "\n".join(parts)


def source_signature(nb: dict) -> str:
    basis = [
        {"cell_type": cell["cell_type"], "source": cell.get("source", [])}
        for cell in nb["cells"]
    ]
    return hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    old = json.loads(FAILED_NB.read_text(encoding="utf-8"))
    req(old["nbformat"] == 4, "failed notebook format drift")
    old_code = [c for c in old["cells"] if c["cell_type"] == "code"]
    req(any(c.get("execution_count") is not None for c in old_code), "preserved first-run notebook is not executed")
    ot = notebook_text(old)
    req(ORIGINAL_LOCK_SHA in ot, "preserved notebook original lock missing")
    req("CalledProcessError" in ot, "preserved notebook failure evidence missing")
    req("PHASE 4 LOCKED TRIAL: EXECUTED" not in notebook_output_text(old), "preserved failed notebook outputs falsely contain success marker")

    amended = json.loads(AMENDED_NB.read_text(encoding="utf-8"))
    req(amended["nbformat"] == 4, "A001 notebook format drift")
    nt = notebook_text(amended)
    for token in (
        AMENDMENT_LOCK_SHA,
        "phase4_colab_amendment001.py",
        "--execute-amendment001-trial",
        "locked_trial_20260829T131721Z",
        "PHASE 4 AMENDMENT 001 TRIAL: EXECUTED",
    ):
        req(token in nt, f"A001 notebook token missing: {token}")

    code = [c for c in amended["cells"] if c["cell_type"] == "code"]
    executed = any(c.get("execution_count") is not None or c.get("outputs") for c in code)
    if not executed:
        for cell in code:
            req(cell.get("execution_count") is None, "A001 pre-execution notebook execution-count drift")
            req(cell.get("outputs") == [], "A001 pre-execution notebook contains outputs")
        notebook_state = "PRE_EXECUTION_LOCKED"
    else:
        out_text = notebook_output_text(amended)
        success = "PHASE 4 AMENDMENT 001 TRIAL: EXECUTED" in out_text
        failed = (
            "CalledProcessError" in out_text
            or "A001 runner failed" in out_text
            or "execution_failure.json" in out_text
        )
        req(success or failed, "A001 post-execution notebook lacks terminal success/failure evidence")
        req(not (success and failed), "A001 notebook contains conflicting terminal states")
        notebook_state = "POST_EXECUTION_SUCCESS" if success else "POST_EXECUTION_FAILED"

    manifest = json.loads(LOCK.read_text())
    req(manifest["amendment_lock_sha256"] == AMENDMENT_LOCK_SHA, "A001 manifest lock mismatch")
    basis = manifest["canonical_basis"]
    computed = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    req(computed == AMENDMENT_LOCK_SHA, "A001 canonical lock digest mismatch")
    req(basis["original_phase3_lock_sha256"] == ORIGINAL_LOCK_SHA, "A001 original-lock identity drift")
    for rel, expected in basis["amended_files_sha256"].items():
        req(sha256(ROOT / rel) == expected, f"A001 locked file drift: {rel}")

    original = json.loads((ROOT / "phase3" / "LOCK_MANIFEST.json").read_text())
    req(original["lock_package_sha256"] == ORIGINAL_LOCK_SHA, "original Phase-3 lock changed")

    runner = (ROOT / "scripts" / "phase4_execute_amendment001.py").read_text()
    for token in (
        "audit_common_site_waveforms",
        "load_flow_rate_matrix_site_local",
        "locked.numerical_audit",
        "p0_reproducibility_gate.json",
        "reference_p0_artifact_sha256",
        "original_load=locked.load_waveform_matrix",
        "locked.load_waveform_matrix=lambda archive,site,signal,expected_active_counts=None: original_load(archive,site,signal)",
        "locked.load_flow_rate_matrix=lambda archive,site,expected_active_counts: load_flow_rate_matrix_site_local(archive,site)[0]",
        "execution_failure.json",
    ):
        req(token in runner, f"A001 runner token missing: {token}")
    req('original_load(archive,site,signal,expected_active_counts)' not in runner, "A001 passes Radial counts into secondary waveform loader")
    req('load_flow_rate_matrix_site_local(archive,site,expected_active_counts)' not in runner, "A001 passes Radial counts into local Q reconstruction")

    amended_io = (ROOT / "src" / "vascularage" / "amendment001_io.py").read_text()
    req("nu == na" in amended_io, "A001 local U/A equality guard missing")
    req("expected_active_counts" not in amended_io, "A001 module must not impose Radial count equality")

    print("Phase 4 Amendment 001 static validation: PASS")
    print("Notebook state:", notebook_state)
    print("Notebook source signature:", source_signature(amended))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
