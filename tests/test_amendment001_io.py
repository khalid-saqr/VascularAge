from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import numpy as np
import pytest

from vascularage.amendment001_io import audit_common_site_waveforms, load_flow_rate_matrix_site_local
from vascularage.confirmatory import COMMON_SITES


def _member_text(active: int, total: int = 4, scale: float = 1.0) -> str:
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["Subject Number", *[f"pt{k}" for k in range(1, total + 1)]])
    values = [str(scale * (k + 1)) for k in range(active)] + ["nan"] * (total - active)
    for sid in range(1, 4375):
        w.writerow([sid, *values])
    return buf.getvalue()


def _write_full_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for site in COMMON_SITES:
            for signal in ("P", "U", "A", "PPG"):
                active = 4 if site == "Radial" else 3
                if site == "Digital" and signal == "PPG":
                    active = 2  # deliberately differs from Digital P/U/A and from Radial
                z.writestr(f"PWs_{site}_{signal}.csv", _member_text(active, scale={"P":1,"U":2,"A":3,"PPG":4}[signal]))


def test_full_52_member_preflight_permits_cross_site_and_unrelated_signal_count_differences(tmp_path):
    archive = tmp_path / "PWs_csv.zip"
    _write_full_archive(archive)
    radial_counts = np.full(4374, 4, dtype=np.int32)
    report = audit_common_site_waveforms(archive, radial_counts)
    assert report["waveform_members_audited"] == 52
    assert report["sites"]["Digital"]["signals"]["PPG"]["subjects_differing_from_radial"] == 4374
    assert report["sites"]["Digital"]["all_four_raw_counts_equal_observed_not_required"] is False
    assert all(site["local_U_A_support_equal"] for site in report["sites"].values())


def test_site_local_flow_reconstruction_does_not_require_radial_count(tmp_path):
    archive = tmp_path / "flow.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("PWs_Carotid_U.csv", _member_text(3, scale=2.0))
        z.writestr("PWs_Carotid_A.csv", _member_text(3, scale=3.0))
    q, counts = load_flow_rate_matrix_site_local(archive, "Carotid")
    assert q.shape == (4374, 512)
    assert np.all(counts == 3)
    assert np.isfinite(q).all()


def test_site_local_flow_rejects_U_A_support_mismatch(tmp_path):
    archive = tmp_path / "flow_bad.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("PWs_Carotid_U.csv", _member_text(3, scale=2.0))
        z.writestr("PWs_Carotid_A.csv", _member_text(2, scale=3.0))
    with pytest.raises(AssertionError, match="local U/A support mismatch"):
        load_flow_rate_matrix_site_local(archive, "Carotid")