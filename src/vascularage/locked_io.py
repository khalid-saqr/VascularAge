"""Locked PWDB loading/preparation for the confirmatory trial.

No file is opened on import. These functions implement the already-qualified
Phase-1 source semantics and may be called only by the guarded Phase-4 runner.
"""
from __future__ import annotations
import csv, io, math, zipfile
from pathlib import Path, PurePosixPath
import numpy as np
from .confirmatory import PHASE_POINTS, SAMPLE_RATE_HZ, AGES, FACTOR_ORDER, cycle_duration_ms, phase_resample_periodic

EXPECTED_IDS=tuple(str(i) for i in range(1,4375))
SOURCE_FACTOR={"HR":"HR","SV":"SV","LVET":"LVET","DIA":"DIA","PWV":"PWV","MAP":"MBP"}
VARIATION_HEADER=("SUBJECT NUMBER","AGE","DIA","HR","LVET","MBP","PWV","SV")

def _require(c,m):
    if not c: raise AssertionError(m)

def load_variations(path: Path):
    rows=[]
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,skipinitialspace=True)
        _require(tuple(str(x).strip() for x in (r.fieldnames or ()))==VARIATION_HEADER,"variation header drift")
        for raw in r:
            row={str(k).strip():str(v).strip() for k,v in raw.items()}
            if any(row.values()): rows.append(row)
    _require(len(rows)==4374 and tuple(x["SUBJECT NUMBER"] for x in rows)==EXPECTED_IDS,"variation identity drift")
    ages=np.array([int(float(x["AGE"])) for x in rows],dtype=np.int16)
    xi=np.array([[int(float(x[SOURCE_FACTOR[f]])) for f in FACTOR_ORDER] for x in rows],dtype=np.int8)
    _require(set(ages.tolist())==set(AGES) and all((ages==a).sum()==729 for a in AGES),"age design drift")
    _require(np.isin(xi,[-1,0,1]).all(),"factor level drift")
    return ages,xi

def _wave_member(archive:zipfile.ZipFile, site:str, signal:str):
    base=f"PWs_{site}_{signal}.csv"
    hits=[i for i in archive.infolist() if not i.is_dir() and PurePosixPath(i.filename).name==base]
    _require(len(hits)==1,f"wave member mismatch {base}")
    return hits[0]

def _parse_row_tokens(tokens):
    vals=[]; missing=[]
    for t in tokens:
        s=t.strip()
        if s=="" or s.lower()=="nan":
            vals.append(math.nan); missing.append(True)
        else:
            v=float(s); _require(math.isfinite(v),"non-finite waveform value")
            vals.append(v); missing.append(False)
    last=max((k for k,m in enumerate(missing) if not m),default=-1)
    _require(last>=1,"fewer than two active waveform samples")
    padding=[m and k>last for k,m in enumerate(missing)]
    internal=[m and not p for m,p in zip(missing,padding,strict=True)]
    _require(not any(internal),"internal missing waveform sample")
    active=np.array([not m for m in missing],dtype=bool)
    arr=np.asarray(vals,dtype=np.float64)[active]
    _require(np.isfinite(arr).all(),"active waveform sample non-finite")
    return arr,int(active.sum())

def load_waveform_matrix(archive_path:Path, site:str, signal:str, expected_active_counts:np.ndarray|None=None):
    """Load SOURCE P/U/A/PPG and periodic-resample each complete cycle."""
    out=np.empty((4374,PHASE_POINTS),dtype=np.float32); counts=np.empty(4374,dtype=np.int32)
    with zipfile.ZipFile(Path(archive_path),"r") as z:
        info=_wave_member(z,site,signal)
        with z.open(info,"r") as raw:
            r=csv.reader(io.TextIOWrapper(raw,encoding="utf-8-sig",newline=""),skipinitialspace=True)
            header=tuple(x.strip() for x in next(r)); _require(header and header[0]=="Subject Number","wave identity header")
            row=0
            for fields in r:
                if not fields or all(not x.strip() for x in fields): continue
                _require(fields[0].strip()==EXPECTED_IDS[row],"wave subject alignment")
                arr,n=_parse_row_tokens(fields[1:])
                counts[row]=n; out[row]=phase_resample_periodic(arr).astype(np.float32)
                row+=1
    _require(row==4374,"wave subject count")
    if expected_active_counts is not None:
        _require(np.array_equal(counts,np.asarray(expected_active_counts,dtype=np.int32)),f"{site} {signal} cycle counts differ from P0")
    return out,counts

def load_flow_rate_matrix(archive_path:Path, site:str, expected_active_counts:np.ndarray):
    """Reconstruct Q=U*A on aligned SOURCE samples, then phase-resample Q."""
    out=np.empty((4374,PHASE_POINTS),dtype=np.float32)
    with zipfile.ZipFile(Path(archive_path),"r") as z:
        iu=_wave_member(z,site,"U"); ia=_wave_member(z,site,"A")
        with z.open(iu,"r") as ru,z.open(ia,"r") as ra:
            u=csv.reader(io.TextIOWrapper(ru,encoding="utf-8-sig",newline=""),skipinitialspace=True)
            a=csv.reader(io.TextIOWrapper(ra,encoding="utf-8-sig",newline=""),skipinitialspace=True)
            hu=next(u); ha=next(a); _require(tuple(hu)==tuple(ha),"U/A header mismatch")
            row=0
            for fu,fa in zip(u,a,strict=True):
                if not fu or all(not x.strip() for x in fu): continue
                _require(fu[0].strip()==fa[0].strip()==EXPECTED_IDS[row],"U/A identity mismatch")
                uv,nu=_parse_row_tokens(fu[1:]); av,na=_parse_row_tokens(fa[1:])
                _require(nu==na==int(expected_active_counts[row]),"U/A/P0 cycle alignment mismatch")
                q=uv*av
                out[row]=phase_resample_periodic(q).astype(np.float32)
                row+=1
    _require(row==4374,"flow-rate subject count")
    return out

def load_scalar_column(path:Path, field:str):
    vals=np.empty(4374,dtype=np.float64); ids=[]
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,skipinitialspace=True)
        fields=tuple(str(x).strip() for x in (r.fieldnames or ()))
        _require(field in fields,f"scalar field missing: {field}")
        sid=next((x for x in fields if x.lower().replace("_"," ").strip() in {"subject number","subject"}),None)
        _require(sid is not None,"scalar subject field missing")
        k=0
        for raw in r:
            row={str(a).strip():str(b).strip() for a,b in raw.items()}
            if not any(row.values()): continue
            ids.append(str(int(float(row[sid])))); vals[k]=float(row[field]); k+=1
    _require(k==4374 and tuple(ids)==EXPECTED_IDS and np.isfinite(vals).all(),"scalar alignment/value drift")
    return vals

def duration_vector_from_counts(counts):
    c=np.asarray(counts,dtype=np.int32)
    _require(c.shape==(4374,),"duration count shape")
    return 1000.0*c.astype(np.float64)/SAMPLE_RATE_HZ
