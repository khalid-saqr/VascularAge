import numpy as np
import pytest

from vascularage.phase1 import nearest_cross_age_numpy, phase_resample, reference_distance, synthetic_qualification


def test_phase_resample_periodic_known_answer():
    got = phase_resample(np.array([0.,1.,2.,3.]), 8)
    assert np.allclose(got, [0.,.5,1.,1.5,2.,2.5,3.,1.5])


def test_reference_distance_boundaries():
    z = np.zeros(512)
    assert np.isclose(reference_distance(z, z+5, 1000, 1000), 1.0)
    assert np.isclose(reference_distance(z, z, 1000, 1010), 1.0)


def test_synthetic_qualification_complete():
    pytest.importorskip("jax")
    result = synthetic_qualification()
    assert all(v is True for k,v in result.items() if k != "jax_max_abs_error")


def test_deterministic_exact_tie_uses_lowest_index():
    phase = np.linspace(0,1,32,endpoint=False)
    base = np.sin(2*np.pi*phase)
    w = np.stack([base, base+5, base, base])
    d = np.full(4,900.0)
    a = np.array([25,25,35,45])
    dist, idx = nearest_cross_age_numpy(w,d,a,block_size=2)
    assert idx[0] == 2
    assert dist[0] == 0
