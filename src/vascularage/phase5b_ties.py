"""Phase-5B tie-sensitivity closure primitives.

These functions operate only on preserved Phase-4 pair/component evidence.
They do not read PWDB waveforms, VascuQuest data, or recompute a biological endpoint.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np

N_SUBJECTS = 4374
N_CROSS_AGE_PAIRS = 7_971_615
TIE_ATOL = 1e-6
PRESSURE_SCALE_MMHG = 5.0
DURATION_SCALE_MS = 10.0
FACTOR_ORDER = ("HR", "SV", "LVET", "DIA", "PWV", "MAP")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def reference_distance_float32(
    pressure_rmse_mmHg: np.ndarray,
    duration_diff_ms: np.ndarray,
) -> np.ndarray:
    """Reproduce the locked Phase-4 reference-distance arithmetic from float32 components."""
    dp = np.asarray(pressure_rmse_mmHg, dtype=np.float32)
    dt = np.asarray(duration_diff_ms, dtype=np.float32)
    _require(dp.shape == dt.shape and dp.ndim == 1, "pair component shape mismatch")
    _require(np.isfinite(dp).all() and np.isfinite(dt).all(), "non-finite pair component")
    return np.sqrt(
        (dp / np.float32(PRESSURE_SCALE_MMHG)) ** 2
        + (dt / np.float32(DURATION_SCALE_MS)) ** 2
    ).astype(np.float32)


@dataclass(frozen=True)
class NearestAudit:
    best_distance: np.ndarray
    canonical_target: np.ndarray
    co_nearest_count: np.ndarray
    second_nearest_gap: np.ndarray


def reconstruct_nearest_from_pairs(
    n_subjects: int,
    i: np.ndarray,
    j: np.ndarray,
    distance: np.ndarray,
    tie_atol: float = TIE_ATOL,
) -> NearestAudit:
    """Reconstruct exact minima and all targets within min+tie_atol.

    The canonical target is the smallest target index inside the co-nearest set,
    matching the locked deterministic convention. second_nearest_gap is the
    distance difference from the exact minimum to the nearest non-canonical target.
    """
    ii = np.asarray(i, dtype=np.int32)
    jj = np.asarray(j, dtype=np.int32)
    dd = np.asarray(distance, dtype=np.float32)
    _require(ii.shape == jj.shape == dd.shape and ii.ndim == 1, "pair table shape mismatch")
    _require(n_subjects > 1, "invalid subject count")
    _require((ii >= 0).all() and (jj >= 0).all(), "negative subject index")
    _require((ii < n_subjects).all() and (jj < n_subjects).all(), "subject index out of range")
    _require(np.isfinite(dd).all(), "non-finite pair distance")
    _require(float(tie_atol) >= 0.0, "tie tolerance must be non-negative")

    best = np.full(n_subjects, np.inf, dtype=np.float32)
    np.minimum.at(best, ii, dd)
    np.minimum.at(best, jj, dd)
    _require(np.isfinite(best).all(), "nearest reconstruction incomplete")

    mi = dd <= (best[ii] + np.float32(tie_atol))
    mj = dd <= (best[jj] + np.float32(tie_atol))
    count = np.zeros(n_subjects, dtype=np.int32)
    np.add.at(count, ii, mi.astype(np.int32))
    np.add.at(count, jj, mj.astype(np.int32))
    _require((count >= 1).all(), "co-nearest set unexpectedly empty")

    sentinel = np.int32(n_subjects)
    target = np.full(n_subjects, sentinel, dtype=np.int32)
    np.minimum.at(target, ii, np.where(mi, jj, sentinel).astype(np.int32))
    np.minimum.at(target, jj, np.where(mj, ii, sentinel).astype(np.int32))
    _require((target < n_subjects).all(), "canonical target reconstruction incomplete")

    gap_i = (dd - best[ii]).astype(np.float32)
    gap_j = (dd - best[jj]).astype(np.float32)
    second = np.full(n_subjects, np.inf, dtype=np.float32)
    np.minimum.at(
        second,
        ii,
        np.where(jj != target[ii], gap_i, np.float32(np.inf)).astype(np.float32),
    )
    np.minimum.at(
        second,
        jj,
        np.where(ii != target[jj], gap_j, np.float32(np.inf)).astype(np.float32),
    )
    _require(np.isfinite(second).all(), "second-nearest reconstruction incomplete")
    _require((second >= 0).all(), "negative nearest/second-nearest gap")

    return NearestAudit(
        best_distance=best,
        canonical_target=target,
        co_nearest_count=count,
        second_nearest_gap=second,
    )


def top_k_motif_concentration(
    vectors: Iterable[Sequence[int]],
    k: int = 20,
) -> tuple[float, int, int]:
    """Return top-k concentration, top-k count, and total vector count."""
    rows = [tuple(int(x) for x in row) for row in vectors]
    _require(len(rows) > 0, "motif vector set is empty")
    _require(all(len(row) == len(FACTOR_ORDER) for row in rows), "motif vector width mismatch")
    counts = Counter(rows)
    top_count = int(sum(sorted(counts.values(), reverse=True)[: int(k)]))
    total = len(rows)
    return float(top_count / total), top_count, total


def bool_from_csv(value: object) -> bool:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def validate_canonical_compensation_rows(
    subject_rows: Sequence[Mapping[str, str]],
    compensation_rows: Sequence[Mapping[str, str]],
) -> dict:
    """Validate that preserved compensation rows use each aliased subject's canonical target."""
    by_id = {int(row["subject_id"]): row for row in subject_rows}
    _require(len(by_id) == N_SUBJECTS, "subject table cardinality mismatch")

    expected_sources = {
        sid for sid, row in by_id.items() if bool_from_csv(row["reference_alias"])
    }
    observed_sources = {int(row["subject_id"]) for row in compensation_rows}
    _require(observed_sources == expected_sources, "compensation source set differs from P0 alias set")

    vectors = []
    for row in compensation_rows:
        sid = int(row["subject_id"])
        tid = int(row["target_subject_id"])
        srow = by_id[sid]
        _require(tid == int(srow["nearest_subject_id"]), f"canonical target mismatch for subject {sid}")
        _require(int(row["source_age"]) == int(srow["age"]), f"source age mismatch for subject {sid}")
        _require(tid in by_id, f"unknown target subject {tid}")
        _require(int(row["target_age"]) == int(by_id[tid]["age"]), f"target age mismatch for subject {sid}")
        vectors.append(tuple(int(row[f"delta_{factor}"]) for factor in FACTOR_ORDER))

    concentration, top_count, total = top_k_motif_concentration(vectors, k=20)
    return {
        "P0_alias_sources": len(expected_sources),
        "compensation_rows": len(compensation_rows),
        "canonical_source_target_rows_match": True,
        "top20_count": top_count,
        "top20_motif_concentration_recomputed": concentration,
        "vector_count": total,
    }
