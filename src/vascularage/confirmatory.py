"""Locked confirmatory analysis primitives for VascularAge Phase 4.

This module is frozen in Phase 3. Importing it never reads PWDB and never
executes a biological endpoint. Phase 4 may call these functions only under
the lock/manifest guard.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
import math
from typing import Mapping, Sequence
import numpy as np

PHASE_POINTS = 512
SAMPLE_RATE_HZ = 500.0
AGES = (25, 35, 45, 55, 65, 75)
FACTOR_ORDER = ("HR","SV","LVET","DIA","PWV","MAP")
COMMON_SITES = ("AorticRoot","ThorAorta","AbdAorta","IliacBif","Carotid","SupTemporal",
                "SupMidCerebral","Brachial","Radial","Digital","CommonIliac","Femoral","AntTibial")
RESTRICTED_SITES = ("AorticRoot","Carotid","Radial","Femoral")
TIE_ATOL = 1e-6

def _require(c: bool, m: str) -> None:
    if not c:
        raise AssertionError(m)

def cycle_duration_ms(active_sample_count: int, sample_rate_hz: float = SAMPLE_RATE_HZ) -> float:
    _require(int(active_sample_count) == active_sample_count and active_sample_count >= 2, "active sample count must be integer >=2")
    _require(sample_rate_hz > 0 and math.isfinite(sample_rate_hz), "sample rate invalid")
    return 1000.0 * float(active_sample_count) / float(sample_rate_hz)

def phase_resample_periodic(values: Sequence[float], phase_points: int = PHASE_POINTS) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    _require(x.ndim == 1 and x.size >= 2 and np.isfinite(x).all(), "active waveform invalid")
    _require(phase_points >= 2, "phase_points must be >=2")
    n = x.size
    old_phase = np.arange(n + 1, dtype=np.float64) / float(n)
    periodic = np.concatenate([x, x[:1]])
    new_phase = np.arange(phase_points, dtype=np.float64) / float(phase_points)
    return np.interp(new_phase, old_phase, periodic)

def rms(x: np.ndarray, axis=None):
    a = np.asarray(x)
    return np.sqrt(np.mean(a*a, axis=axis))

def pressure_rmse(a: Sequence[float], b: Sequence[float]) -> float:
    x=np.asarray(a,dtype=np.float64); y=np.asarray(b,dtype=np.float64)
    _require(x.shape==y.shape and x.ndim==1 and np.isfinite(x).all() and np.isfinite(y).all(), "pressure waveform invalid")
    return float(np.sqrt(np.mean((x-y)**2)))

def symmetric_relative_rms(a: Sequence[float], b: Sequence[float], floor: float = 1e-12) -> float:
    x=np.asarray(a,dtype=np.float64); y=np.asarray(b,dtype=np.float64)
    _require(x.shape==y.shape and x.ndim==1 and np.isfinite(x).all() and np.isfinite(y).all(), "relative-rms waveform invalid")
    denom=float(np.sqrt(0.5*(np.mean(x*x)+np.mean(y*y))))
    return float(np.sqrt(np.mean((x-y)**2))/max(denom,floor))

def standardize_ppg_shape(x: Sequence[float], floor: float = 1e-12) -> np.ndarray:
    a=np.asarray(x,dtype=np.float64)
    _require(a.ndim==1 and np.isfinite(a).all(), "PPG invalid")
    c=a-a.mean()
    scale=float(np.sqrt(np.mean(c*c)))
    _require(scale>floor, "PPG has zero/near-zero dynamic content")
    return c/scale

def ppg_shape_rmse(a: Sequence[float], b: Sequence[float]) -> float:
    x=standardize_ppg_shape(a); y=standardize_ppg_shape(b)
    _require(x.shape==y.shape, "PPG shapes mismatch")
    return float(np.sqrt(np.mean((x-y)**2)))

def elliptical_distance(component: float, duration_diff_ms: float, component_scale: float, duration_scale_ms: float) -> float:
    _require(component_scale>0 and duration_scale_ms>0, "scales must be positive")
    return float(np.sqrt((float(component)/component_scale)**2 + (float(duration_diff_ms)/duration_scale_ms)**2))

def pair_alias_primary(dp_mmHg: float, dt_ms: float, eP: float=5.0, eT: float=10.0) -> bool:
    return elliptical_distance(dp_mmHg, dt_ms, eP, eT) <= 1.0

def pair_alias_ppg(shape_rmse: float, dt_ms: float, eShape: float=0.20, eT: float=10.0) -> bool:
    return elliptical_distance(shape_rmse, dt_ms, eShape, eT) <= 1.0

def pwv_relative_difference(x: float, y: float, floor: float=1e-12) -> float:
    return 2.0*abs(float(x)-float(y))/max(abs(float(x))+abs(float(y)), floor)

def conventional_composite_alias(pwv_i:float,pwv_j:float,aix_i:float,aix_j:float,sbp_i:float,sbp_j:float) -> bool:
    return pwv_relative_difference(pwv_i,pwv_j) <= 0.05 and abs(aix_i-aix_j) <= 5.0 and abs(sbp_i-sbp_j) <= 5.0

def unordered_age_pair_indices(ages: Sequence[int]):
    a=np.asarray(ages)
    _require(a.ndim==1, "ages must be 1-D")
    out=[]
    for age_a,age_b in combinations(AGES,2):
        ia=np.flatnonzero(a==age_a); ib=np.flatnonzero(a==age_b)
        _require(ia.size==729 and ib.size==729, f"age block mismatch {age_a},{age_b}")
        out.append((age_a,age_b,ia,ib))
    return out

def pair_components_numpy(waveforms: np.ndarray, durations_ms: np.ndarray, ages: np.ndarray):
    """Return all unordered cross-age pair indices and P0 components."""
    w=np.asarray(waveforms,dtype=np.float64); d=np.asarray(durations_ms,dtype=np.float64); a=np.asarray(ages)
    _require(w.shape==(4374,PHASE_POINTS) and d.shape==(4374,) and a.shape==(4374,), "canonical shapes required")
    ii=[]; jj=[]; dp=[]; dt=[]
    for _,_,ia,ib in unordered_age_pair_indices(a):
        x=w[ia]; y=w[ib]
        diff=x[:,None,:]-y[None,:,:]
        block=np.sqrt(np.mean(diff*diff,axis=2))
        dur=np.abs(d[ia,None]-d[None,ib])
        gi=np.repeat(ia, ib.size); gj=np.tile(ib, ia.size)
        ii.append(gi.astype(np.int32)); jj.append(gj.astype(np.int32))
        dp.append(block.reshape(-1).astype(np.float32)); dt.append(dur.reshape(-1).astype(np.float32))
    return np.concatenate(ii),np.concatenate(jj),np.concatenate(dp),np.concatenate(dt)

def reference_pair_distance(dp: np.ndarray, dt: np.ndarray, eP:float=5.0,eT:float=10.0) -> np.ndarray:
    return np.sqrt((np.asarray(dp)/eP)**2 + (np.asarray(dt)/eT)**2)

def subject_alias_exists(n_subjects:int, i:np.ndarray,j:np.ndarray,pair_alias:np.ndarray) -> np.ndarray:
    out=np.zeros(n_subjects,dtype=bool)
    mask=np.asarray(pair_alias,dtype=bool)
    out[np.asarray(i)[mask]]=True; out[np.asarray(j)[mask]]=True
    return out

def canonical_nearest_from_pairs(n_subjects:int,i:np.ndarray,j:np.ndarray,dist:np.ndarray,tie_atol:float=TIE_ATOL):
    """Deterministic directed nearest cross-age target from unordered pair table."""
    i=np.asarray(i,dtype=np.int32); j=np.asarray(j,dtype=np.int32); d=np.asarray(dist,dtype=np.float64)
    best=np.full(n_subjects,np.inf); target=np.full(n_subjects,-1,dtype=np.int32); ties=np.zeros(n_subjects,dtype=np.int32)
    # first pass exact minima
    for left,right,val in zip(i,j,d,strict=True):
        if val < best[left]-tie_atol: best[left]=val; target[left]=right; ties[left]=1
        elif val <= best[left]+tie_atol:
            ties[left]+=1
            if target[left] < 0 or right < target[left]: target[left]=right
        if val < best[right]-tie_atol: best[right]=val; target[right]=left; ties[right]=1
        elif val <= best[right]+tie_atol:
            ties[right]+=1
            if target[right] < 0 or left < target[right]: target[right]=left
    _require(np.isfinite(best).all() and (target>=0).all(), "nearest search incomplete")
    return best,target,ties

def alias_surface(i,j,dp,dt,n_subjects:int=4374,eP_grid=(1,2,3,5,8,10),eT_grid=(2,5,10,20)):
    rows=[]
    for ep in eP_grid:
        for et in eT_grid:
            mask=reference_pair_distance(dp,dt,float(ep),float(et))<=1.0
            subj=subject_alias_exists(n_subjects,i,j,mask)
            rows.append((float(ep),float(et),int(mask.sum()),int(subj.sum()),float(subj.mean())))
    return rows

def jaccard_bool(a: Sequence[bool], b: Sequence[bool]) -> float:
    x=np.asarray(a,dtype=bool); y=np.asarray(b,dtype=bool)
    inter=np.logical_and(x,y).sum(); union=np.logical_or(x,y).sum()
    return 1.0 if union==0 else float(inter/union)

def compensation_vectors(xi: np.ndarray, source_indices: np.ndarray, target_indices: np.ndarray) -> np.ndarray:
    x=np.asarray(xi,dtype=np.int8); s=np.asarray(source_indices,dtype=np.int32); t=np.asarray(target_indices,dtype=np.int32)
    _require(x.shape==(4374,6), "xi shape must be 4374x6")
    return (x[t]-x[s]).astype(np.int8)

def top_k_motif_concentration(vectors: np.ndarray, k:int=20) -> float:
    v=np.asarray(vectors,dtype=np.int8); _require(v.ndim==2 and v.shape[1]==6 and len(v)>0, "motif vectors invalid")
    _,counts=np.unique(v,axis=0,return_counts=True)
    return float(np.sort(counts)[::-1][:k].sum()/len(v))

def compensation_null(source_idx:np.ndarray,target_ages:np.ndarray,ages:np.ndarray,xi:np.ndarray,permutations:int=10000,seed:int=20260829,k:int=20):
    s=np.asarray(source_idx,dtype=np.int32); ta=np.asarray(target_ages); a=np.asarray(ages); x=np.asarray(xi,dtype=np.int8)
    rng=np.random.default_rng(seed); pools={age:np.flatnonzero(a==age) for age in AGES}
    vals=np.empty(permutations,dtype=np.float64)
    for r in range(permutations):
        t=np.array([rng.choice(pools[int(age)]) for age in ta],dtype=np.int32)
        vals[r]=top_k_motif_concentration(x[t]-x[s],k=k)
    return vals

def local_information_metric(stencil: Mapping[str,tuple[np.ndarray,float,np.ndarray,float]], pressure_scale:float=5.0,duration_scale:float=10.0):
    """stencil factor -> (minus_P, minus_T_ms, plus_P, plus_T_ms)."""
    cols=[]
    for f in FACTOR_ORDER:
        pm,tm,pp,tp=stencil[f]
        pm=np.asarray(pm,dtype=np.float64); pp=np.asarray(pp,dtype=np.float64)
        _require(pm.shape==(PHASE_POINTS,) and pp.shape==(PHASE_POINTS,), f"stencil shape {f}")
        zm=np.concatenate([pm/(math.sqrt(PHASE_POINTS)*pressure_scale),[float(tm)/duration_scale]])
        zp=np.concatenate([pp/(math.sqrt(PHASE_POINTS)*pressure_scale),[float(tp)/duration_scale]])
        cols.append((zp-zm)/2.0)
    J=np.stack(cols,axis=1)
    F=J.T@J
    eigvals,eigvecs=np.linalg.eigh(F)
    positive=eigvals[eigvals>1e-14]
    cond=float(np.inf if positive.size==0 or eigvals[0]<=1e-14 else eigvals[-1]/eigvals[0])
    return {"J":J,"F":F,"eigenvalues":eigvals,"eigenvectors":eigvecs,"condition_number":cond,"weakest_direction":eigvecs[:,0]}

@dataclass(frozen=True)
class RescueComponent:
    quantity: str
    distance: np.ndarray  # one value per candidate pair

def nested_rescue_masks(p0_alias:np.ndarray, components_by_arm:Mapping[str,Sequence[RescueComponent]], eP:float=5.0,eRel:float=0.05):
    """Pair-level survivor masks for nested M1-M4 among P0 reference aliases."""
    base=np.asarray(p0_alias,dtype=bool)
    survivor=base.copy(); out={}
    for arm in ("M1","M2","M3","M4"):
        for c in components_by_arm.get(arm,()):
            if c.quantity=="pressure":
                survivor &= np.asarray(c.distance)<=eP
            elif c.quantity in {"luminal_area","flow_rate_reconstructed"}:
                survivor &= np.asarray(c.distance)<=eRel
            else:
                raise AssertionError(f"unsupported rescue quantity {c.quantity}")
        out[arm]=survivor.copy()
    return out

def rescue_fraction_by_subject(n_subjects:int,i,j,p0_alias,richer_alias):
    p0=subject_alias_exists(n_subjects,i,j,p0_alias)
    rich=subject_alias_exists(n_subjects,i,j,richer_alias)
    denom=int(p0.sum())
    return 0.0 if denom==0 else float(np.logical_and(p0,~rich).sum()/denom)


def age_pair_components_jax(waveforms, durations_ms, ia, ib):
    """JAX/XLA 729x729 P0 component block; direct differences avoid quadratic-form cancellation."""
    import jax
    import jax.numpy as jnp
    w=jnp.asarray(waveforms,dtype=jnp.float32); d=jnp.asarray(durations_ms,dtype=jnp.float32)
    ia=jnp.asarray(ia,dtype=jnp.int32); ib=jnp.asarray(ib,dtype=jnp.int32)
    @jax.jit
    def kernel():
        x=w[ia]; y=w[ib]
        diff=x[:,None,:]-y[None,:,:]
        dp=jnp.sqrt(jnp.mean(diff*diff,axis=2))
        dt=jnp.abs(d[ia,None]-d[ib][None,:])
        return dp,dt
    return kernel()

def selected_pair_distance_jax(waveforms, i, j, mode:str):
    """Distance for selected candidate pairs, used only after P0 candidate filtering."""
    import jax
    import jax.numpy as jnp
    w=jnp.asarray(waveforms,dtype=jnp.float32); ii=jnp.asarray(i,dtype=jnp.int32); jj=jnp.asarray(j,dtype=jnp.int32)
    @jax.jit
    def kernel(ii_b,jj_b):
        x=w[ii_b]; y=w[jj_b]
        if mode=="pressure":
            return jnp.sqrt(jnp.mean((x-y)**2,axis=1))
        if mode in ("luminal_area","flow_rate_reconstructed"):
            num=jnp.sqrt(jnp.mean((x-y)**2,axis=1))
            den=jnp.sqrt(0.5*(jnp.mean(x*x,axis=1)+jnp.mean(y*y,axis=1)))
            return num/jnp.maximum(den,jnp.asarray(1e-12,dtype=den.dtype))
        if mode=="ppg_shape":
            xc=x-jnp.mean(x,axis=1,keepdims=True); yc=y-jnp.mean(y,axis=1,keepdims=True)
            xs=xc/jnp.maximum(jnp.sqrt(jnp.mean(xc*xc,axis=1,keepdims=True)),1e-12)
            ys=yc/jnp.maximum(jnp.sqrt(jnp.mean(yc*yc,axis=1,keepdims=True)),1e-12)
            return jnp.sqrt(jnp.mean((xs-ys)**2,axis=1))
        raise ValueError(mode)
    return kernel(ii,jj)

__all__=[name for name in globals() if not name.startswith("_")]
