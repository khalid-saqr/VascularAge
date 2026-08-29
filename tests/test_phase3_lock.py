import json, math
from pathlib import Path
import numpy as np
import pytest

from vascularage.confirmatory import (
    AGES, COMMON_SITES, FACTOR_ORDER, cycle_duration_ms, phase_resample_periodic,
    symmetric_relative_rms, ppg_shape_rmse, pair_alias_primary,
    canonical_nearest_from_pairs, local_information_metric,
    conventional_composite_alias, jaccard_bool, age_pair_components_jax,
)

ROOT=Path(__file__).resolve().parents[1]

def test_locked_config_invariants():
    cfg=json.loads((ROOT/"phase3"/"LOCKED_TRIAL_CONFIG.json").read_text())
    assert cfg["biological_endpoints_allowed_in_phase3"] is False
    assert cfg["dataset"]["expected_subjects"]==4374
    assert cfg["dataset"]["ages"]==list(AGES)
    assert cfg["dataset"]["factor_order"]==list(FACTOR_ORDER)
    assert len(cfg["primary"]["pressure_tolerance_grid_mmHg"])*len(cfg["primary"]["duration_tolerance_grid_ms"])==24
    assert cfg["primary"]["reference"]=={"pressure_mmHg":5.0,"duration_ms":10.0}
    assert cfg["measurement_rescue"]["evaluation_order"]==["M1","M2","M3","M4"]
    assert cfg["measurement_rescue"]["arms"]["M4"]["sites_all_common"]==list(COMMON_SITES)
    assert cfg["compensation"]["random_seed"]==20260829
    assert cfg["numerics"]["production_dtype"]=="float32"

def test_period_and_periodic_resampling():
    assert cycle_duration_ms(500)==1000.0
    n=125
    x=np.sin(2*np.pi*np.arange(n)/n)
    y=phase_resample_periodic(x,512)
    assert y.shape==(512,)
    assert np.isfinite(y).all()
    assert abs(y[0]-x[0])<1e-12

def test_reference_alias_boundary():
    assert pair_alias_primary(5.0,0.0)
    assert pair_alias_primary(0.0,10.0)
    assert not pair_alias_primary(5.0,10.0)

def test_relative_and_ppg_operators():
    assert symmetric_relative_rms([1,2,3],[1,2,3])==pytest.approx(0)
    assert ppg_shape_rmse([1,2,3,4],[2,4,6,8])==pytest.approx(0,abs=1e-12)

def test_nearest_tie_break_is_smallest_target_index():
    i=np.array([0,0,1,1,2,2],dtype=np.int32)
    j=np.array([1,2,2,3,3,4],dtype=np.int32)
    d=np.array([0.5,0.5,0.7,0.4,0.3,0.2])
    best,target,ties=canonical_nearest_from_pairs(5,i,j,d)
    assert target[0]==1
    assert ties[0]==2
    assert np.isfinite(best).all()

def test_information_metric_recovers_known_null_direction():
    stencil={}
    for k,f in enumerate(FACTOR_ORDER):
        v=np.zeros(512)
        if k<5: v[k]=1
        stencil[f]=(-v,1000.0,v,1000.0)
    g=local_information_metric(stencil)
    assert g["F"].shape==(6,6)
    assert g["eigenvalues"][0] < 1e-12

def test_conventional_benchmark_and_jaccard():
    assert conventional_composite_alias(10,10.4,20,24,120,124)
    assert jaccard_bool([1,0,1],[1,1,0])==pytest.approx(1/3)

def test_jax_age_pair_components_matches_numpy():
    pytest.importorskip("jax")
    rng=np.random.default_rng(7)
    w=rng.normal(size=(7,512)).astype(np.float32)
    d=np.array([900,910,920,1000,1010,1020,1030],dtype=np.float32)
    ia=np.array([0,1,2],dtype=np.int32); ib=np.array([3,4,5,6],dtype=np.int32)
    dp,dt=age_pair_components_jax(w,d,ia,ib)
    dp=np.asarray(dp); dt=np.asarray(dt)
    ref=np.sqrt(np.mean((w[ia,None,:]-w[None,ib,:])**2,axis=2))
    refdt=np.abs(d[ia,None]-d[None,ib])
    assert np.allclose(dp,ref,rtol=1e-5,atol=1e-6)
    assert np.array_equal(dt,refdt)
