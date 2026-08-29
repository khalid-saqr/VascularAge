import numpy as np
import pytest

from vascularage.phase5b_ties import (
    TIE_ATOL,
    bool_from_csv,
    reconstruct_nearest_from_pairs,
    reference_distance_float32,
    top_k_motif_concentration,
)


def complete_four(distances):
    i = np.array([0, 0, 0, 1, 1, 2], dtype=np.int32)
    j = np.array([1, 2, 3, 2, 3, 3], dtype=np.int32)
    return i, j, np.asarray(distances, dtype=np.float32)


def test_reference_distance_matches_locked_geometry():
    dp = np.array([5.0, 0.0, 3.0], dtype=np.float32)
    dt = np.array([0.0, 10.0, 8.0], dtype=np.float32)
    got = reference_distance_float32(dp, dt)
    assert got[0] == pytest.approx(1.0)
    assert got[1] == pytest.approx(1.0)
    assert got[2] == pytest.approx(1.0)


def test_unique_nearest_sets_and_canonical_targets():
    i, j, d = complete_four([0.2, 0.5, 0.8, 0.6, 0.7, 0.3])
    out = reconstruct_nearest_from_pairs(4, i, j, d)
    assert out.co_nearest_count.tolist() == [1, 1, 1, 1]
    assert out.canonical_target.tolist() == [1, 0, 3, 2]
    assert out.second_nearest_gap[0] == pytest.approx(0.3)
    assert out.second_nearest_gap[2] == pytest.approx(0.2)


def test_co_nearest_within_locked_tolerance_is_detected():
    i, j, d = complete_four([0.2, 0.2000005, 0.8, 0.6, 0.7, 0.3])
    out = reconstruct_nearest_from_pairs(4, i, j, d, tie_atol=TIE_ATOL)
    assert out.co_nearest_count[0] == 2
    assert out.canonical_target[0] == 1


def test_candidate_just_outside_tolerance_is_not_a_tie():
    i, j, d = complete_four([0.2, 0.200002, 0.8, 0.6, 0.7, 0.3])
    out = reconstruct_nearest_from_pairs(4, i, j, d, tie_atol=TIE_ATOL)
    assert out.co_nearest_count[0] == 1
    assert out.canonical_target[0] == 1


def test_top_k_motif_concentration_known_answer():
    vectors = [
        (1, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0),
        (0, 1, 0, 0, 0, 0),
    ]
    concentration, count, total = top_k_motif_concentration(vectors, k=1)
    assert concentration == pytest.approx(0.75)
    assert count == 3
    assert total == 4


@pytest.mark.parametrize(
    ("value", "expected"),
    [("True", True), ("false", False), ("1", True), ("0", False)],
)
def test_csv_boolean_parser(value, expected):
    assert bool_from_csv(value) is expected
