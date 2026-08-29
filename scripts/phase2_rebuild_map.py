#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

CORE_FIELDS = ['Authors','Author full names','Author(s) ID','Title','Year','Source title','Volume','Issue','Art. No.','Page start','Page end','DOI','Link','Abstract','Open Access','EID']
EXPECTED_ROWS = 889
EXPECTED_RAW_SHA256 = "80714d21233d79cfcb02e0012e4bcc2faa31a711eb77610f5983f66adf81f5fc"
EXPECTED_CORE_SHA256 = "6a032e13b10ee799a7773f59bdf5661310d0243472890faf97615cfde3933a31"
NEGATIVE_SEED = 20260829

def require(c, m):
    if not c: raise AssertionError(m)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source', required=True); ap.add_argument('--phase2-dir', default='phase2'); args=ap.parse_args()
    source=Path(args.source); out=Path(args.phase2_dir); raw=source.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==EXPECTED_RAW_SHA256, 'frozen source hash mismatch')
    df=pd.read_csv(source).fillna(''); require(len(df)==EXPECTED_ROWS, 'row count mismatch'); require(all(x in df.columns for x in CORE_FIELDS), 'core field missing')
    core=df[CORE_FIELDS].copy(); core_bytes=core.to_csv(index=False,lineterminator='\n').encode(); require(hashlib.sha256(core_bytes).hexdigest()==EXPECTED_CORE_SHA256, 'canonical core hash mismatch')
    ontology=json.loads((out/'ontology.json').read_text(encoding='utf-8')); axis_order=ontology['axis_bit_order']; require(axis_order==list(ontology['axes'].keys()), 'axis bit order drift')
    text=(core['Title'].astype(str)+' '+core['Abstract'].astype(str)).str.lower(); axes={name:text.str.contains(ontology['axes'][name]['regex'], regex=True, na=False) for name in axis_order}; ax=pd.DataFrame(axes)
    old_high=df['Threat_class'].astype(str).str.startswith(('P1','P2')); candidate=ax['vascular_age_assessment'] | (ax['ageing_context'] & ax['arterial_pulse_wave']) | old_high
    expected=pd.concat([pd.read_csv(p) for p in sorted((out/'evidence_map').glob('evidence_map_*.csv'))], ignore_index=True); require(expected['record_index'].tolist()==list(range(EXPECTED_ROWS)), 'evidence map indices mismatch')
    masks=[format(sum((int(ax.iloc[i][name])&1)<<bit for bit,name in enumerate(axis_order)),'04x') for i in range(EXPECTED_ROWS)]; require(expected['axis_mask_hex'].astype(str).str.zfill(4).tolist()==masks, 'axis bitmask drift'); require(expected['high_relevance'].astype(int).tolist()==candidate.astype(int).tolist(), 'candidate set drift')
    audit=pd.concat([pd.read_csv(p) for p in sorted((out/'collision_audit').glob('collision_audit_*.csv'))], ignore_index=True); require(sorted(audit['record_index'].astype(int).tolist())==list(np.where(candidate)[0]), 'collision audit coverage mismatch')
    remaining=np.where(~candidate.to_numpy())[0]; rng=np.random.default_rng(NEGATIVE_SEED); neg=np.sort(rng.choice(remaining,size=50,replace=False)); negfile=pd.read_csv(out/'negative_control_audit_50.csv'); require(negfile['record_index'].astype(int).tolist()==neg.tolist(), 'negative-control sample drift')
    print('Phase 2 frozen-corpus rebuild validation: PASS'); print('source_sha256', EXPECTED_RAW_SHA256); print('core_sha256', EXPECTED_CORE_SHA256); print('candidate_records', int(candidate.sum())); return 0
if __name__=='__main__': raise SystemExit(main())
