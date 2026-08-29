"""Phase-4 Amendment 001 source semantics.

The original Phase-3 locked files remain immutable.  This module implements
only the formally amended site-local waveform-support rule:

* every ordinary waveform is validated on its own active source support;
* raw active-count equality across anatomical sites/signals is not required;
* reconstructed Q=U*A requires local U/A sample-support equality only;
* all morphology comparisons still meet on the locked 512-point phase grid;
* subject duration remains defined exclusively by P0 Radial pressure.
"""
from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import numpy as np

from .confirmatory import COMMON_SITES, PHASE_POINTS, phase_resample_periodic
from .locked_io import EXPECTED_IDS, _parse_row_tokens, _wave_member, load_waveform_matrix

SIGNALS = ("P", "U", "A", "PPG")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _active_count_vector_from_archive(archive: zipfile.ZipFile, site: str, signal: str) -> np.ndarray:
    """Count valid active support without converting the waveform numerics.

    Phase 1 already qualified numeric finiteness.  A001 preflight needs the
    support topology: subject identity, trailing padding, and absence of
    internal missing values.  Avoiding float conversion makes the complete
    52-member audit practical while preserving exactly those checks.
    """
    counts = np.empty(4374, dtype=np.int32)
    info = _wave_member(archive, site, signal)
    with archive.open(info, "r") as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), skipinitialspace=True)
        header = tuple(x.strip() for x in next(reader))
        _require(header and header[0] == "Subject Number", f"{site} {signal} identity header")
        row = 0
        for fields in reader:
            if not fields or all(not x.strip() for x in fields):
                continue
            _require(row < 4374, f"{site} {signal} extra subject row")
            _require(fields[0].strip() == EXPECTED_IDS[row], f"{site} {signal} subject alignment")
            tokens = fields[1:]
            missing = [(not t.strip()) or t.strip().lower() == "nan" for t in tokens]
            last = max((k for k, is_missing in enumerate(missing) if not is_missing), default=-1)
            _require(last >= 1, f"{site} {signal} fewer than two active samples")
            _require(not any(missing[: last + 1]), f"{site} {signal} internal missing sample subject {row + 1}")
            counts[row] = last + 1
            row += 1
    _require(row == 4374, f"{site} {signal} subject count")
    return counts


def active_count_vector(archive_path: Path, site: str, signal: str) -> np.ndarray:
    with zipfile.ZipFile(Path(archive_path), "r") as archive:
        return _active_count_vector_from_archive(archive, site, signal)


def audit_common_site_waveforms(archive_path: Path, radial_counts: np.ndarray) -> dict:
    """Audit all 52 common-site waveform members before amended biological work.

    Cross-site count differences are observed and reported, not rejected.
    Local U/A equality is mandatory because Q=U*A is a pointwise reconstruction.
    """
    radial = np.asarray(radial_counts, dtype=np.int32)
    _require(radial.shape == (4374,), "radial count shape")
    sites: dict[str, dict] = {}
    with zipfile.ZipFile(Path(archive_path), "r") as archive:
        for site in COMMON_SITES:
            per_signal = {sig: _active_count_vector_from_archive(archive, site, sig) for sig in SIGNALS}
            _require(np.array_equal(per_signal["U"], per_signal["A"]), f"{site} local U/A support mismatch")
            sites[site] = {
                "signals": {
                    sig: {
                        "min_active_samples": int(v.min()),
                        "max_active_samples": int(v.max()),
                        "subjects_differing_from_radial": int(np.count_nonzero(v != radial)),
                        "max_abs_sample_count_difference_from_radial": int(np.max(np.abs(v - radial))),
                    }
                    for sig, v in per_signal.items()
                },
                "local_U_A_support_equal": True,
                "all_four_raw_counts_equal_observed_not_required": bool(
                    np.array_equal(per_signal["P"], per_signal["U"])
                    and np.array_equal(per_signal["P"], per_signal["A"])
                    and np.array_equal(per_signal["P"], per_signal["PPG"])
                ),
            }
    return {
        "amendment": "A001",
        "rule": "site-local active support; no cross-site raw-count equality; U/A equality required only for Q=U*A",
        "common_sites": len(COMMON_SITES),
        "waveform_members_audited": len(COMMON_SITES) * len(SIGNALS),
        "subjects_per_member": 4374,
        "sites": sites,
    }


def load_flow_rate_matrix_site_local(archive_path: Path, site: str) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct Q=U*A on the site's own aligned source support, then phase-resample."""
    out = np.empty((4374, PHASE_POINTS), dtype=np.float32)
    counts = np.empty(4374, dtype=np.int32)
    with zipfile.ZipFile(Path(archive_path), "r") as archive:
        iu = _wave_member(archive, site, "U")
        ia = _wave_member(archive, site, "A")
        with archive.open(iu, "r") as raw_u, archive.open(ia, "r") as raw_a:
            u_reader = csv.reader(io.TextIOWrapper(raw_u, encoding="utf-8-sig", newline=""), skipinitialspace=True)
            a_reader = csv.reader(io.TextIOWrapper(raw_a, encoding="utf-8-sig", newline=""), skipinitialspace=True)
            hu = tuple(x.strip() for x in next(u_reader))
            ha = tuple(x.strip() for x in next(a_reader))
            _require(hu == ha, f"{site} U/A header mismatch")
            row = 0
            for fu, fa in zip(u_reader, a_reader, strict=True):
                if not fu or all(not x.strip() for x in fu):
                    _require(not fa or all(not x.strip() for x in fa), f"{site} U/A blank-row mismatch")
                    continue
                _require(row < 4374, f"{site} U/A extra subject row")
                _require(fu[0].strip() == fa[0].strip() == EXPECTED_IDS[row], f"{site} U/A identity mismatch")
                uv, nu = _parse_row_tokens(fu[1:])
                av, na = _parse_row_tokens(fa[1:])
                _require(nu == na, f"{site} local U/A support mismatch subject {row + 1}")
                _require(uv.shape == av.shape, f"{site} local U/A array mismatch subject {row + 1}")
                counts[row] = nu
                out[row] = phase_resample_periodic(uv * av).astype(np.float32)
                row += 1
    _require(row == 4374, f"{site} flow-rate subject count")
    return out, counts


def load_component_site_local(archive_path: Path, site: str, quantity: str):
    """Load a rescue component under Amendment 001 semantics."""
    if quantity == "pressure":
        return load_waveform_matrix(archive_path, site, "P")[0], "pressure"
    if quantity == "luminal_area":
        return load_waveform_matrix(archive_path, site, "A")[0], "luminal_area"
    if quantity == "flow_rate_reconstructed":
        return load_flow_rate_matrix_site_local(archive_path, site)[0], "flow_rate_reconstructed"
    raise AssertionError(quantity)
