"""Phase-5 S2 robustness primitives.

Importing this module does not read PWDB and does not execute a biological
endpoint.  Scientific definitions are locked by phase5/S2_LOCK.json.
"""
from __future__ import annotations
import numpy as np

PHASE_POINTS = 512
N_SUBJECTS = 4374
PRESSURE_SCALE_MMHG = 5.0
DURATION_SCALE_MS = 10.0
JACCARD_THRESHOLD = 0.50


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def l1_pressure(a, b) -> float:
    """Sample-normalised discrete L1 pressure discrepancy (mean absolute error)."""
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    _require(x.shape == y.shape and x.ndim == 1, "L1 pressure shape mismatch")
    _require(np.isfinite(x).all() and np.isfinite(y).all(), "L1 pressure non-finite")
    return float(np.mean(np.abs(x - y)))


def linf_pressure(a, b) -> float:
    """Discrete L-infinity pressure discrepancy."""
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    _require(x.shape == y.shape and x.ndim == 1, "Linf pressure shape mismatch")
    _require(np.isfinite(x).all() and np.isfinite(y).all(), "Linf pressure non-finite")
    return float(np.max(np.abs(x - y)))


def matched_distance(pressure_metric, duration_diff_ms,
                     pressure_scale_mmHg: float = PRESSURE_SCALE_MMHG,
                     duration_scale_ms: float = DURATION_SCALE_MS):
    _require(pressure_scale_mmHg > 0 and duration_scale_ms > 0, "scales must be positive")
    p = np.asarray(pressure_metric)
    dt = np.asarray(duration_diff_ms)
    return np.sqrt((p / pressure_scale_mmHg) ** 2 + (dt / duration_scale_ms) ** 2)


def subject_alias_exists(i, j, pair_alias, n_subjects: int = N_SUBJECTS) -> np.ndarray:
    ii = np.asarray(i, dtype=np.int32)
    jj = np.asarray(j, dtype=np.int32)
    mask = np.asarray(pair_alias, dtype=bool)
    _require(ii.shape == jj.shape == mask.shape, "pair arrays mismatch")
    out = np.zeros(n_subjects, dtype=bool)
    out[ii[mask]] = True
    out[jj[mask]] = True
    return out


def jaccard_bool(a, b) -> float:
    x = np.asarray(a, dtype=bool)
    y = np.asarray(b, dtype=bool)
    _require(x.shape == y.shape, "Jaccard set shape mismatch")
    union = np.logical_or(x, y).sum()
    return 1.0 if union == 0 else float(np.logical_and(x, y).sum() / union)


def adjudicate_s2(j_l1: float, j_linf: float, threshold: float = JACCARD_THRESHOLD) -> bool:
    """Return True exactly when the prospectively locked S2 NO-GO fires."""
    _require(0 <= j_l1 <= 1 and 0 <= j_linf <= 1, "Jaccard outside [0,1]")
    _require(0 < threshold < 1, "invalid S2 threshold")
    return bool(j_l1 < threshold and j_linf < threshold)


def age_pair_metrics_jax(waveforms, ia, ib):
    """Return float32 729x729 L1 and L-infinity blocks on the active JAX backend."""
    import jax
    import jax.numpy as jnp

    w = jnp.asarray(waveforms, dtype=jnp.float32)
    ia = jnp.asarray(ia, dtype=jnp.int32)
    ib = jnp.asarray(ib, dtype=jnp.int32)

    @jax.jit
    def kernel():
        x = w[ia]
        y = w[ib]
        diff = jnp.abs(x[:, None, :] - y[None, :, :])
        return jnp.mean(diff, axis=2), jnp.max(diff, axis=2)

    return kernel()


def selected_metrics_float64(waveforms, i, j, chunk_size: int = 4096):
    """Independent NumPy float64 recomputation for selected pair rows."""
    w = np.asarray(waveforms, dtype=np.float64)
    ii = np.asarray(i, dtype=np.int32)
    jj = np.asarray(j, dtype=np.int32)
    _require(w.shape == (N_SUBJECTS, PHASE_POINTS), "canonical waveform shape required")
    _require(ii.shape == jj.shape, "selected pair shape mismatch")
    l1 = np.empty(ii.size, dtype=np.float64)
    linf = np.empty(ii.size, dtype=np.float64)
    for start in range(0, ii.size, chunk_size):
        stop = min(start + chunk_size, ii.size)
        d = np.abs(w[ii[start:stop]] - w[jj[start:stop]])
        l1[start:stop] = np.mean(d, axis=1)
        linf[start:stop] = np.max(d, axis=1)
    return l1, linf
