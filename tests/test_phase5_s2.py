import numpy as np
import pytest

from vascularage.phase5_s2 import (
    adjudicate_s2,
    jaccard_bool,
    l1_pressure,
    linf_pressure,
    matched_distance,
    selected_metrics_float64,
    subject_alias_exists,
)


def test_l1_and_linf_known_answer():
    a = np.array([0.0, 2.0, 4.0, 8.0])
    b = np.array([0.0, 1.0, 7.0, 6.0])
    assert l1_pressure(a, b) == pytest.approx(1.5)
    assert linf_pressure(a, b) == pytest.approx(3.0)


def test_l1_is_sample_normalised_not_raw_sum():
    a = np.zeros(512)
    b = np.ones(512) * 5.0
    assert l1_pressure(a, b) == pytest.approx(5.0)
    assert l1_pressure(a, b) != pytest.approx(2560.0)


def test_matched_distance_reference_geometry():
    assert matched_distance(5.0, 0.0) == pytest.approx(1.0)
    assert matched_distance(0.0, 10.0) == pytest.approx(1.0)
    assert matched_distance(3.0, 8.0) == pytest.approx(1.0)


def test_subject_alias_and_jaccard():
    i = np.array([0, 0, 1, 2], dtype=np.int32)
    j = np.array([1, 2, 3, 3], dtype=np.int32)
    a = subject_alias_exists(i, j, np.array([True, False, False, False]), n_subjects=4)
    b = subject_alias_exists(i, j, np.array([False, True, False, False]), n_subjects=4)
    assert a.tolist() == [True, True, False, False]
    assert b.tolist() == [True, False, True, False]
    assert jaccard_bool(a, b) == pytest.approx(1 / 3)


def test_s2_boolean_rule_is_strict_and_conjunctive():
    assert adjudicate_s2(0.49, 0.49) is True
    assert adjudicate_s2(0.50, 0.49) is False
    assert adjudicate_s2(0.49, 0.50) is False
    assert adjudicate_s2(0.50, 0.50) is False


def test_selected_float64_metrics():
    w = np.zeros((4374, 512), dtype=np.float64)
    w[1] = 2.0
    w[2, 100] = 8.0
    l1, linf = selected_metrics_float64(w, np.array([0, 0]), np.array([1, 2]))
    assert l1[0] == pytest.approx(2.0)
    assert linf[0] == pytest.approx(2.0)
    assert l1[1] == pytest.approx(8.0 / 512.0)
    assert linf[1] == pytest.approx(8.0)
