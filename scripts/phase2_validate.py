#!/usr/bin/env python3
from __future__ import annotations
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; P2=ROOT/'phase2'
def require(c,m):
    if not c: raise AssertionError(m)
def rows(path):
    with path.open('r',encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def main():
    manifest=json.loads((P2/'CORPUS_MANIFEST.json').read_text(encoding='utf-8')); summary=json.loads((P2/'summary.json').read_text(encoding='utf-8')); ontology=json.loads((P2/'ontology.json').read_text(encoding='utf-8'))
    ep=sorted((P2/'evidence_map').glob('evidence_map_*.csv')); cp=sorted((P2/'collision_audit').glob('collision_audit_*.csv')); require(len(ep)==4,'expected four evidence-map parts'); require(len(cp)==4,'expected four collision-audit parts')
    em=sum((rows(p) for p in ep), []); ca=sum((rows(p) for p in cp), []); nc=rows(P2/'negative_control_audit_50.csv'); ex=rows(P2/'external_collision_audit.csv')
    require(manifest['source_rows']==889,'manifest row count'); require(manifest['source_sha256']=='80714d21233d79cfcb02e0012e4bcc2faa31a711eb77610f5983f66adf81f5fc','source hash drift'); require(manifest['canonical_core_sha256']=='6a032e13b10ee799a7773f59bdf5661310d0243472890faf97615cfde3933a31','core hash drift'); require(manifest['original_scopus_query_status']=='not_preserved','query limitation must remain explicit')
    require(ontology['axis_bit_order']==list(ontology['axes'].keys()),'axis order drift'); require(len(em)==889,'evidence map must contain 889 records'); require([int(x['record_index']) for x in em]==list(range(889)),'record index/order drift'); require(all(len(x['axis_mask_hex'])<=4 for x in em),'invalid bitmask width')
    require(len(ca)==111,'collision audit must contain 111 records'); require(len(set(int(x['record_index']) for x in ca))==111,'collision audit duplicate index'); require(not any(x['collision_class']=='C0_direct_collision' for x in ca),'unexpected fixed-corpus direct collision')
    require(len(nc)==50 and len(set(int(x['record_index']) for x in nc))==50,'negative-control audit invalid'); require(all(x['audit_status']=='true_negative_for_locked_concept' for x in nc),'negative-control adjudication incomplete'); require(len(ex)>=10,'external collision audit unexpectedly small'); require(not any(x['collision_class']=='C0_direct_collision' for x in ex),'external direct collision requires Phase-3 novelty review')
    require(summary['biological_endpoint_executed'] is False,'biological leakage flag'); require(summary['meta_analysis_performed'] is False,'meta-analysis flag'); require(summary['direct_collision_identified'] is False,'direct collision flag')
    required=['README.md','CORPUS_MANIFEST.json','SCREENING_PROTOCOL.md','ontology.json','negative_control_audit_50.csv','external_collision_audit.csv','TARGETED_SEARCH_LOG.md','NOVELTY_STATEMENT.md','REVIEW_LIMITATIONS.md','EVIDENCE_FLOW.md','summary.json']; [require((P2/r).exists(),f'missing {r}') for r in required]
    forbidden={'Title','Abstract','Authors','Author full names'}
    for path in ep+cp+[P2/'negative_control_audit_50.csv']:
        data=rows(path)
        if data: require(not (forbidden & set(data[0])),f'raw bibliographic text redistributed in {path}')
    print('Phase 2 repository validation: PASS'); print(json.dumps({'frozen_records':len(em),'collision_audit':len(ca),'negative_controls':len(nc),'external_collision_sources':len(ex),'direct_collisions':0,'biological_endpoint_executed':False},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
