#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

import numpy as np

from vascularage.phase1 import (
    audit_model_variations,
    audit_radial_archive,
    crosscheck_radial_vascuquest,
    dump_json,
    require,
    synthetic_qualification,
)

ALLOW_BIOLOGICAL_ENDPOINTS = False
SAMPLE_SUBJECTS = (
    "1", "729", "730", "1458", "1459", "2187",
    "2188", "2916", "2917", "3645", "3646", "4374",
)


def pkg_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run(args: argparse.Namespace) -> int:
    require(ALLOW_BIOLOGICAL_ENDPOINTS is False, "biological endpoint guard changed")
    drive_root = Path(args.drive_root)
    repo_root = Path(args.repo_root)
    vq_repo_root = Path(args.vq_repo_root)
    qual = drive_root / "qualification_v2"
    qual.mkdir(parents=True, exist_ok=True)

    contract_path = repo_root / "phase1" / "qualification_contract.json"
    contract_bytes = contract_path.read_bytes()
    observed_contract_sha = hashlib.sha256(contract_bytes).hexdigest()
    contract = json.loads(contract_bytes)
    require(contract["biological_endpoints_allowed"] is False, "contract permits biological endpoints")

    repo_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    vq_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vq_repo_root, text=True).strip()
    require(vq_commit == contract["vascuquest"]["commit_sha"], "VascuQuest commit mismatch")

    pytest_run = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=repo_root, capture_output=True, text=True)
    print(pytest_run.stdout)
    if pytest_run.stderr:
        print(pytest_run.stderr, file=sys.stderr)
    require(pytest_run.returncode == 0, "repository tests failed")

    import jax
    import vascuquest as vq
    from vascuquest.data import ArtifactAcquirer, DataPaths, SourceRegistry, verify_artifact
    from vascuquest.domain import MeasurementSite
    from vascuquest.schema import load_manifest

    tier4_path = qual / "vascuquest_tier4_core.json"
    tier4_run = subprocess.run([
        sys.executable,
        str(vq_repo_root / "tests" / "full_data" / "core_release_validation.py"),
        "--report", str(tier4_path),
        "--code-revision", contract["vascuquest"]["commit_sha"],
        "--repo-root", str(vq_repo_root),
    ], capture_output=True, text=True)
    print(tier4_run.stdout)
    if tier4_run.stderr:
        print(tier4_run.stderr, file=sys.stderr)
    require(tier4_run.returncode == 0, "VascuQuest Tier-4 validation failed")

    tier4 = json.loads(tier4_path.read_text(encoding="utf-8"))
    require(tier4.get("status") == "passed", "VascuQuest Tier-4 report status is not passed")
    scalar = tier4["scalar_source_validation"]
    waveform = tier4["waveform_archive_validation"]
    api = tier4["public_api_and_science_validation"]
    require(scalar["age_group_counts"] == {str(a): 729 for a in (25,35,45,55,65,75)}, "Tier-4 age groups mismatch")
    require(waveform["declared_members"] == 52 and waveform["all_members_subject_aligned"] is True, "Tier-4 waveform inventory mismatch")
    require(api["subjects"] == 4374, "Tier-4 public subject count mismatch")
    require(api["flow_rate_reconstruction"]["real_source_identity_check"] == "Q=U*A on parsed source arrays", "Tier-4 Q=U*A validation mismatch")

    paths = DataPaths.default()
    manifest = load_manifest()
    registry = SourceRegistry(paths.state_file("sources.json"))
    acquirer = ArtifactAcquirer(paths, registry, manifest=manifest)

    variations_path = acquirer.acquire("model_variations", offline=False)
    variation_spec = manifest.artifact("model_variations")
    variation_check = verify_artifact(variations_path, variation_spec)
    require(variation_check.state.value == "verified", "model_variations checksum verification failed")
    require(variation_check.observed_checksum == variation_spec.checksum_value, "model_variations checksum mismatch")

    model_config_path = paths.source_artifact(manifest.artifact("model_configurations").filename)
    waveform_path = paths.source_artifact(manifest.artifact("common_site_waveforms_csv").filename)

    factorial = audit_model_variations(variations_path, model_config_path)
    radial = audit_radial_archive(waveform_path, SAMPLE_SUBJECTS)

    session = vq.open_dataset(source=paths.source, offline=True)
    radial_crosscheck = crosscheck_radial_vascuquest(session, radial, MeasurementSite)

    source_qualification = {
        "layer": "A+B",
        "status": "PASS",
        "vascuquest_tier4": {
            "status": "passed",
            "age_group_counts": scalar["age_group_counts"],
            "waveform_members": waveform["declared_members"],
            "all_waveform_members_subject_aligned": waveform["all_members_subject_aligned"],
            "public_subjects": api["subjects"],
            "flow_rate_q_equals_u_times_a": True,
        },
        "model_variations": {
            "filename": variation_spec.filename,
            "checksum_algorithm": variation_spec.checksum_algorithm,
            "expected_checksum": variation_spec.checksum_value,
            "observed_checksum": variation_check.observed_checksum,
            "size_bytes": variation_check.size_bytes,
            "factorial_audit": factorial,
        },
        "radial_pressure": radial,
        "radial_vascuquest_crosscheck": radial_crosscheck,
        "biological_endpoint_executed": False,
    }
    dump_json(qual / "source_qualification.json", source_qualification)

    engine = synthetic_qualification()
    engine_qualification = {
        "layer": "C",
        "status": "PASS",
        "checks": engine,
        "jax_backend": jax.default_backend(),
        "jax_devices": [str(d) for d in jax.devices()],
        "biological_endpoint_executed": False,
    }
    dump_json(qual / "engine_qualification.json", engine_qualification)

    environment = {
        "layer": "D",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "jax": jax.__version__,
        "jaxlib": pkg_version("jaxlib"),
        "jax_backend": jax.default_backend(),
        "jax_devices": [str(d) for d in jax.devices()],
        "vascuquest": pkg_version("vascuquest"),
        "vascuquest_commit": vq_commit,
        "vascularage_repo_commit": repo_commit,
        "contract_sha256": observed_contract_sha,
        "drive_root": str(drive_root),
        "biological_endpoint_executed": False,
    }
    dump_json(qual / "environment.json", environment)

    summary = {
        "phase": 1,
        "status": "PASS",
        "contract_version": contract["contract_version"],
        "contract_sha256": observed_contract_sha,
        "vascularage_repo_commit": repo_commit,
        "vascuquest_commit": vq_commit,
        "source_qualification": "PASS",
        "engine_qualification": "PASS",
        "biological_endpoint_executed": False,
        "next_phase_authorized_by_notebook": False,
    }
    dump_json(qual / "qualification_summary.json", summary)

    report = f"""# Phase 1 External Colab Qualification — Rebuild v2

- Status: **PASS**
- VascularAge commit: `{repo_commit}`
- VascuQuest commit: `{vq_commit}`
- Contract: `2.0` / `{observed_contract_sha}`
- JAX backend: `{jax.default_backend()}`
- Canonical PWDB simulations qualified: **4,374**
- Factorial design verified: **6 ages × 729 = 4,374; 729 = 3^6**
- Primary radial waveform semantics: **VascuQuest blank/NaN missing + trailing padding semantics**
- Radial internal missing samples: **{radial['internal_missing_total']}**
- Radial active-sample range: **{radial['min_active_samples']}–{radial['max_active_samples']}**
- Biological cross-age endpoint executed: **No**

No real-PWDB cross-age distance, nearest alias, alias prevalence, age-identifiability surface,
compensation vector, or measurement-rescue result was calculated in Phase 1.
"""
    (qual / "PHASE_1_RUN_REPORT.md").write_text(report, encoding="utf-8")

    names = [x for x in contract["outputs"] if x != "bundle_hashes.json"]
    hashes = {name: hashlib.sha256((qual / name).read_bytes()).hexdigest() for name in names}
    dump_json(qual / "bundle_hashes.json", hashes)

    print("=" * 72)
    print("PHASE 1 QUALIFICATION: PASS")
    print("=" * 72)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("Qualification bundle:", qual)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive-root", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--vq-repo-root", required=True)
    args = parser.parse_args()
    qual = Path(args.drive_root) / "qualification_v2"
    try:
        return run(args)
    except Exception as exc:
        qual.mkdir(parents=True, exist_ok=True)
        failure = {
            "phase": 1,
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "biological_endpoint_executed": False,
        }
        dump_json(qual / "qualification_failure.json", failure)
        print(json.dumps(failure, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
