from __future__ import annotations

import csv
import io
import json
import math
from itertools import product
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

import numpy as np

EXPECTED_SUBJECT_IDS = tuple(str(i) for i in range(1, 4375))
EXPECTED_AGES = (25, 35, 45, 55, 65, 75)
EXPECTED_LEVELS = (-1, 0, 1)
EXPECTED_VARIATION_HEADER = ("SUBJECT NUMBER", "AGE", "DIA", "HR", "LVET", "MBP", "PWV", "SV")
PROTOCOL_FACTOR_ORDER = ("HR", "SV", "LVET", "DIA", "PWV", "MAP")
SOURCE_FACTOR_COLUMNS = {"HR": "HR", "SV": "SV", "LVET": "LVET", "DIA": "DIA", "PWV": "PWV", "MAP": "MBP"}
RADIAL_MEMBER = "PWs_Radial_P.csv"
SAMPLE_RATE_HZ = 500.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _clean_row(raw: dict[str, object]) -> dict[str, str]:
    return {str(k).strip(): "" if v is None else str(v).strip() for k, v in raw.items()}


def audit_model_variations(variations_path: Path, model_configs_path: Path) -> dict[str, object]:
    """Validate the checksum-verified canonical variation artifact's actual schema."""
    rows: list[dict[str, str]] = []
    with variations_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, skipinitialspace=True)
        require(reader.fieldnames is not None, "model variations header missing")
        header = tuple(str(x).strip() for x in reader.fieldnames)
        require(header == EXPECTED_VARIATION_HEADER, f"unexpected model variations header: {header}")
        for raw in reader:
            row = _clean_row(raw)
            if any(row.values()):
                rows.append(row)

    require(len(rows) == 4374, f"expected 4374 variation rows, got {len(rows)}")
    require(tuple(r["SUBJECT NUMBER"] for r in rows) == EXPECTED_SUBJECT_IDS, "variation subject order mismatch")

    source_columns = tuple(SOURCE_FACTOR_COLUMNS[f] for f in PROTOCOL_FACTOR_ORDER)
    expected_states = set(product(EXPECTED_LEVELS, repeat=6))
    age_summary: dict[str, dict[str, object]] = {}

    for age in EXPECTED_AGES:
        group = [r for r in rows if int(float(r["AGE"])) == age]
        require(len(group) == 729, f"age {age}: expected 729 rows, got {len(group)}")
        states = [tuple(int(float(r[c])) for c in source_columns) for r in group]
        require(all(v in EXPECTED_LEVELS for state in states for v in state), f"age {age}: factor outside -1/0/+1")
        require(len(set(states)) == 729 and set(states) == expected_states, f"age {age}: incomplete 3^6 design")
        age_summary[str(age)] = {"subjects": 729, "unique_states": 729, "complete_3pow6": True}

    config_age: dict[str, int] = {}
    with model_configs_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, skipinitialspace=True)
        require(reader.fieldnames is not None, "model configurations header missing")
        fields = tuple(str(x).strip() for x in reader.fieldnames)
        subject_field = next((x for x in fields if x.lower().replace("_", " ") in {"subject number", "subject"}), None)
        age_field = next((x for x in fields if x.lower() == "age [years]"), None)
        require(subject_field is not None and age_field is not None, f"unexpected model configuration fields: {fields}")
        for raw in reader:
            row = _clean_row(raw)
            if any(row.values()):
                config_age[row[subject_field]] = int(float(row[age_field]))
    require(tuple(config_age) == EXPECTED_SUBJECT_IDS, "model configuration subject order mismatch")
    require(all(config_age[r["SUBJECT NUMBER"]] == int(float(r["AGE"])) for r in rows), "age mismatch between source tables")

    return {
        "subjects": 4374,
        "ages": list(EXPECTED_AGES),
        "header": list(header),
        "protocol_factor_order": list(PROTOCOL_FACTOR_ORDER),
        "source_columns_in_protocol_order": list(source_columns),
        "factor_source_mapping": dict(SOURCE_FACTOR_COLUMNS),
        "age_groups": age_summary,
        "map_to_source_mbp_explicit": True,
        "age_alignment_with_model_configs": True,
    }


def _parse_missing_token(text: str) -> tuple[bool, float]:
    stripped = text.strip()
    if stripped == "" or stripped.lower() == "nan":
        return True, math.nan
    try:
        value = float(stripped)
    except ValueError as exc:
        raise AssertionError(f"non-numeric waveform sample {text!r}") from exc
    require(math.isfinite(value), f"waveform sample contains non-finite non-NaN value {text!r}")
    return False, value


def audit_radial_archive(archive_path: Path, sample_subjects: tuple[str, ...]) -> dict[str, object]:
    """Stream Radial pressure using the same missing/padding semantics as VascuQuest."""
    sampled: dict[str, dict[str, object]] = {}
    active_counts: list[int] = []
    padding_counts: list[int] = []
    internal_missing_total = 0

    with zipfile.ZipFile(archive_path, "r") as archive:
        matches = [i for i in archive.infolist() if not i.is_dir() and PurePosixPath(i.filename).name == RADIAL_MEMBER]
        require(len(matches) == 1, f"expected one {RADIAL_MEMBER}, got {len(matches)}")
        with archive.open(matches[0], "r") as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""), skipinitialspace=True)
            try:
                header = tuple(x.strip() for x in next(reader))
            except StopIteration as exc:
                raise AssertionError("radial pressure source is empty") from exc
            require(header and header[0] == "Subject Number", "radial pressure identity field mismatch")
            points = header[1:]
            require(points == tuple(f"pt{i}" for i in range(1, len(points) + 1)), "radial pressure sample columns noncanonical")

            row_index = 0
            for values in reader:
                if not values or all(not x.strip() for x in values):
                    continue
                require(len(values) == len(header), f"radial row {row_index+2}: field-count mismatch")
                require(row_index < 4374, "radial pressure has more than 4374 subjects")
                subject = values[0].strip()
                require(subject == EXPECTED_SUBJECT_IDS[row_index], f"radial subject alignment failure at row {row_index+2}")

                missing_flags: list[bool] = []
                parsed: list[float] = []
                for token in values[1:]:
                    missing, value = _parse_missing_token(token)
                    missing_flags.append(missing)
                    parsed.append(value)

                last_present = -1
                for idx, missing in enumerate(missing_flags):
                    if not missing:
                        last_present = idx
                require(last_present >= 1, f"subject {subject}: fewer than two active radial samples")

                padding = [bool(m and idx > last_present) for idx, m in enumerate(missing_flags)]
                internal_missing = [bool(m and not p) for m, p in zip(missing_flags, padding, strict=True)]
                active = [not m for m in missing_flags]
                require(all(math.isfinite(v) for v, is_active in zip(parsed, active, strict=True) if is_active), f"subject {subject}: active radial sample not finite")

                active_count = sum(active)
                padding_count = sum(padding)
                internal_count = sum(internal_missing)
                active_counts.append(active_count)
                padding_counts.append(padding_count)
                internal_missing_total += internal_count

                if subject in sample_subjects:
                    sampled[subject] = {
                        "active_samples": active_count,
                        "padding_samples": padding_count,
                        "internal_missing_samples": internal_count,
                        "total_sample_columns": len(points),
                    }
                row_index += 1

    require(row_index == 4374, f"radial pressure expected 4374 subjects, got {row_index}")
    require(internal_missing_total == 0, f"radial pressure contains {internal_missing_total} internal missing samples; Phase 0 requires amendment before resampling")
    require(set(sampled) == set(sample_subjects), "radial audit did not capture all cross-check subjects")
    return {
        "member": RADIAL_MEMBER,
        "subjects": row_index,
        "sample_columns": len(points),
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "all_subjects_aligned": True,
        "missing_padding_semantics": "blank or NaN = missing; missing after last present = padding; earlier missing = internal missing",
        "internal_missing_total": internal_missing_total,
        "min_active_samples": min(active_counts),
        "max_active_samples": max(active_counts),
        "min_padding_samples": min(padding_counts),
        "max_padding_samples": max(padding_counts),
        "sampled_subjects": sampled,
        "cycle_duration_candidate": "N_active / 500 seconds; final convention locks in Phase 3",
    }


def crosscheck_radial_vascuquest(session: object, raw_audit: dict[str, object], measurement_site_cls: object) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    for subject, expected in raw_audit["sampled_subjects"].items():
        wave = session.waveform("pressure", subject=subject, location=measurement_site_cls("Radial"))
        values = np.asarray(wave.values, dtype=float)
        missing = np.asarray(wave.missing_mask, dtype=bool)
        padding = np.asarray(wave.padding_mask, dtype=bool)
        require(wave.quantity.canonical_name == "pressure", f"subject {subject}: VascuQuest quantity mismatch")
        require(wave.canonical_unit == "mmHg", f"subject {subject}: VascuQuest pressure unit mismatch")
        require(wave.evidence.value == "SOURCE", f"subject {subject}: VascuQuest evidence mismatch")
        require(values.shape == missing.shape == padding.shape, f"subject {subject}: VascuQuest waveform/mask shape mismatch")
        require(not np.any(missing & padding), f"subject {subject}: VascuQuest missing/padding overlap")
        active = ~(missing | padding)
        require(np.isfinite(values[active]).all(), f"subject {subject}: active VascuQuest radial sample is non-finite")
        require(int(active.sum()) == expected["active_samples"], f"subject {subject}: active-count mismatch raw vs VascuQuest")
        require(int(missing.sum()) == expected["internal_missing_samples"], f"subject {subject}: internal-missing mismatch raw vs VascuQuest")
        require(int(padding.sum()) == expected["padding_samples"], f"subject {subject}: padding mismatch raw vs VascuQuest")
        checks.append({
            "subject": subject,
            "active_samples": int(active.sum()),
            "missing_samples": int(missing.sum()),
            "padding_samples": int(padding.sum()),
            "unit": wave.canonical_unit,
            "evidence": wave.evidence.value,
        })
    return {"pass": True, "subjects": checks}


def phase_resample(values, phase_points: int = 512) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    require(x.ndim == 1 and x.size >= 2, "phase_resample expects a one-dimensional cycle with >=2 samples")
    require(np.isfinite(x).all(), "phase_resample received non-finite active samples")
    require(phase_points >= 2, "phase_points must be >=2")
    n = x.size
    old_phase = np.arange(n + 1, dtype=np.float64) / n
    periodic = np.concatenate([x, x[:1]])
    new_phase = np.arange(phase_points, dtype=np.float64) / phase_points
    return np.interp(new_phase, old_phase, periodic)


def reference_distance(p_i, p_j, duration_i_ms, duration_j_ms, pressure_scale_mmHg: float = 5.0, duration_scale_ms: float = 10.0) -> float:
    a = np.asarray(p_i, dtype=np.float64)
    b = np.asarray(p_j, dtype=np.float64)
    require(a.shape == b.shape, "pressure waveforms must align")
    dp = float(np.sqrt(np.mean((a - b) ** 2)))
    dt = abs(float(duration_i_ms) - float(duration_j_ms))
    return float(np.sqrt((dp / pressure_scale_mmHg) ** 2 + (dt / duration_scale_ms) ** 2))


def nearest_cross_age_numpy(waveforms, durations_ms, ages, block_size: int = 256, tie_atol: float = 1e-6):
    w = np.asarray(waveforms, dtype=np.float64)
    d = np.asarray(durations_ms, dtype=np.float64)
    a = np.asarray(ages)
    n = w.shape[0]
    require(w.ndim == 2 and d.shape == (n,) and a.shape == (n,), "nearest-search shapes invalid")
    out_d = np.full(n, np.inf, dtype=np.float64)
    out_i = np.full(n, -1, dtype=np.int32)
    for start in range(0, n, block_size):
        stop = min(start + block_size, n)
        diff = w[start:stop, None, :] - w[None, :, :]
        dp = np.sqrt(np.mean(diff * diff, axis=2))
        dt = np.abs(d[start:stop, None] - d[None, :])
        dist = np.sqrt((dp / 5.0) ** 2 + (dt / 10.0) ** 2)
        dist[a[start:stop, None] == a[None, :]] = np.inf
        row_min = np.min(dist, axis=1)
        candidate = dist <= row_min[:, None] + tie_atol
        indices = np.arange(n, dtype=np.int32)[None, :]
        idx = np.min(np.where(candidate, indices, n), axis=1)
        val = dist[np.arange(stop-start), idx]
        out_d[start:stop] = val
        out_i[start:stop] = idx
    return out_d, out_i


def nearest_cross_age_jax(waveforms, durations_ms, ages, block_size: int = 256, tie_atol: float = 1e-6):
    import jax
    import jax.numpy as jnp
    w = jnp.asarray(waveforms)
    d = jnp.asarray(durations_ms)
    a = jnp.asarray(ages)
    n = int(w.shape[0])
    all_idx = jnp.arange(n, dtype=jnp.int32)[None, :]
    sentinel = jnp.asarray(n, dtype=jnp.int32)

    @jax.jit
    def kernel(tw, td, ta):
        diff = tw[:, None, :] - w[None, :, :]
        dp = jnp.sqrt(jnp.mean(diff * diff, axis=2))
        dt = jnp.abs(td[:, None] - d[None, :])
        dist = jnp.sqrt((dp / 5.0) ** 2 + (dt / 10.0) ** 2)
        dist = jnp.where(ta[:, None] == a[None, :], jnp.inf, dist)
        row_min = jnp.min(dist, axis=1)
        candidate = dist <= row_min[:, None] + tie_atol
        idx = jnp.min(jnp.where(candidate, all_idx, sentinel), axis=1)
        val = jnp.take_along_axis(dist, idx[:, None], axis=1)[:, 0]
        return val, idx

    vals, inds = [], []
    for start in range(0, n, block_size):
        stop = min(start + block_size, n)
        vals_i, inds_i = kernel(w[start:stop], d[start:stop], a[start:stop])
        vals.append(vals_i)
        inds.append(inds_i)
    return jnp.concatenate(vals), jnp.concatenate(inds)


def fisher_information(jacobian: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    j = np.asarray(jacobian, dtype=np.float64)
    require(j.ndim == 2 and sigma > 0, "invalid Fisher inputs")
    return (j.T @ j) / (sigma ** 2)


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def synthetic_qualification() -> dict[str, object]:
    phase = np.linspace(0, 1, 64, endpoint=False)
    base = 90 + 10*np.sin(2*np.pi*phase)
    waves = np.stack([base, base+8, base, base+16, base+8, base+24]).astype(np.float32)
    durations = np.full(6, 900.0, dtype=np.float32)
    ages = np.array([25,25,35,35,45,45], dtype=np.int32)

    nd, ni = nearest_cross_age_numpy(waves, durations, ages, block_size=2)
    jd, ji = nearest_cross_age_jax(waves, durations, ages, block_size=2)
    jd = np.asarray(jd)
    ji = np.asarray(ji)
    require(np.allclose(nd, jd, rtol=2e-5, atol=2e-5), "NumPy/JAX distance mismatch")
    require(np.array_equal(ni, ji), "NumPy/JAX nearest-index mismatch")
    require(nd[0] < 1e-7 and int(ni[0]) == 2, "known alias not recovered")

    sep_waves = np.stack([base + k*30 for k in range(6)]).astype(np.float32)
    sep_ages = np.array([25,35,45,55,65,75], dtype=np.int32)
    sd, _ = nearest_cross_age_numpy(sep_waves, durations, sep_ages, block_size=2)
    require(np.all(sd > 1.0), "known separated system not separated")

    secondary = np.zeros_like(waves)
    secondary[2] += 30
    primary = reference_distance(waves[0], waves[2], durations[0], durations[2])
    combined = math.sqrt(primary**2 + float(np.mean((secondary[0]-secondary[2])**2))/25.0)
    require(primary == 0.0 and combined > 1.0, "known rescue failed")

    eig = np.linalg.eigvalsh(fisher_information(np.array([[1.,1.],[2.,2.],[3.,3.]])))
    require(abs(eig[0]) < 1e-10 and eig[-1] > 0, "known Fisher null failed")

    r = phase_resample(np.array([0.,1.,2.,3.]), 8)
    require(np.allclose(r, [0.,.5,1.,1.5,2.,2.5,3.,1.5]), "periodic phase-resample known answer failed")
    require(np.isclose(reference_distance(np.zeros(512), np.ones(512)*5, 1000, 1000), 1.0), "pressure reference boundary failed")
    require(np.isclose(reference_distance(np.zeros(512), np.zeros(512), 1000, 1010), 1.0), "duration reference boundary failed")

    rng = np.random.default_rng(20260828)
    rw = rng.normal(size=(37,64)).astype(np.float32)
    rd = rng.uniform(600,1200,37).astype(np.float32)
    ra = np.array([25]*7+[35]*6+[45]*6+[55]*6+[65]*6+[75]*6, dtype=np.int32)
    n2, i2 = nearest_cross_age_numpy(rw, rd, ra, block_size=8)
    j2, k2 = nearest_cross_age_jax(rw, rd, ra, block_size=8)
    j2 = np.asarray(j2)
    k2 = np.asarray(k2)
    require(np.allclose(n2, j2, rtol=4e-5, atol=4e-5), "random NumPy/JAX distances mismatch")
    require(np.array_equal(i2, k2), "random NumPy/JAX indices mismatch")

    with tempfile.TemporaryDirectory() as tmp:
        checkpoint = Path(tmp) / "checkpoint.json"
        payload = {"phase": 1, "completed_batches": [0, 1, 3], "biological_endpoint_executed": False}
        dump_json(checkpoint, payload)
        require(json.loads(checkpoint.read_text(encoding="utf-8")) == payload, "checkpoint roundtrip failed")

    return {
        "phase_resample_known_answer": True,
        "reference_distance_known_answer": True,
        "known_alias": True,
        "known_separation": True,
        "known_rescue": True,
        "known_fisher_null": True,
        "checkpoint_roundtrip": True,
        "jax_numpy_equivalence": True,
        "jax_max_abs_error": float(np.max(np.abs(n2-j2))),
    }
