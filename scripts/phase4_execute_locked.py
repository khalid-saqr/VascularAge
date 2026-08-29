#!/usr/bin/env python3
"""Execute the locked VascularAge confirmatory trial.

This file is committed and hashed in Phase 3 but MUST NOT be executed in
Phase 3. Phase 4 may invoke it only with the explicit execution flag and an
exact Phase-3 lock-package hash.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, sys
from pathlib import Path
import numpy as np

from vascularage.confirmatory import (
    AGES, COMMON_SITES, FACTOR_ORDER, TIE_ATOL, age_pair_components_jax,
    alias_surface, canonical_nearest_from_pairs, compensation_null,
    compensation_vectors, conventional_composite_alias, jaccard_bool,
    local_information_metric, ppg_shape_rmse, pwv_relative_difference,
    reference_pair_distance, rescue_fraction_by_subject,
    subject_alias_exists, top_k_motif_concentration, unordered_age_pair_indices,
)
from vascularage.locked_io import (
    duration_vector_from_counts, load_flow_rate_matrix, load_scalar_column,
    load_variations, load_waveform_matrix,
)

def req(c,m):
    if not c: raise AssertionError(m)

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_lock(repo:Path, expected_package_sha:str):
    manifest=json.loads((repo/"phase3"/"LOCK_MANIFEST.json").read_text())
    req(manifest["lock_package_sha256"]==expected_package_sha,"lock-package SHA mismatch")
    basis={"parent_main_commit":manifest["parent_main_commit"],
           "upstream_git_blobs":manifest["upstream_git_blobs"],
           "locked_files_sha256":manifest["locked_files_sha256"],
           "external_qualified_execution":manifest["external_qualified_execution"]}
    computed=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    req(computed==manifest["lock_package_sha256"],"lock-package canonical digest mismatch")
    for rel,h in manifest["locked_files_sha256"].items():
        req(sha256(repo/rel)==h,f"locked file hash mismatch: {rel}")
    return manifest

def write_csv(path:Path,fieldnames,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); w.writerows(rows)

def all_pair_components_jax(w,d,a):
    ii=[]; jj=[]; dps=[]; dts=[]
    for _,_,ia,ib in unordered_age_pair_indices(a):
        dp,dt=age_pair_components_jax(w,d,ia,ib)
        dp=np.asarray(dp,dtype=np.float32); dt=np.asarray(dt,dtype=np.float32)
        ii.append(np.repeat(ia,ib.size).astype(np.int32))
        jj.append(np.tile(ib,ia.size).astype(np.int32))
        dps.append(dp.reshape(-1)); dts.append(dt.reshape(-1))
    return np.concatenate(ii),np.concatenate(jj),np.concatenate(dps),np.concatenate(dts)

def selected_chunked(w,i,j,mode,chunk=32768):
    import jax
    import jax.numpy as jnp
    i=np.asarray(i,dtype=np.int32); j=np.asarray(j,dtype=np.int32)
    wd=jnp.asarray(w,dtype=jnp.float32)
    @jax.jit
    def kernel(ii,jj):
        x=wd[ii]; y=wd[jj]
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
    out=np.empty(len(i),dtype=np.float32)
    for q in range(0,len(i),chunk):
        e=min(q+chunk,len(i))
        out[q:e]=np.asarray(kernel(jnp.asarray(i[q:e]),jnp.asarray(j[q:e])),dtype=np.float32)
    return out

def primary_age_pair_rows(ages,i,j,pair_alias):
    rows=[]; off=0; block=729*729
    for aa,bb in __import__("itertools").combinations(AGES,2):
        m=np.asarray(pair_alias[off:off+block],dtype=bool)
        ia=i[off:off+block]; ib=j[off:off+block]
        sa=np.zeros(4374,dtype=bool); sb=np.zeros(4374,dtype=bool)
        sa[ia[m]]=True; sb[ib[m]]=True
        rows.append({"age_a":aa,"age_b":bb,"alias_pairs":int(m.sum()),
                     "fraction_age_a_with_alias":float(sa[np.asarray(ages)==aa].mean()),
                     "fraction_age_b_with_alias":float(sb[np.asarray(ages)==bb].mean()),
                     "mean_directional_fraction":float((sa[np.asarray(ages)==aa].mean()+sb[np.asarray(ages)==bb].mean())/2)})
        off+=block
    return rows

def incremental_rescue_components():
    m3=[("AorticRoot","pressure"),("AorticRoot","flow_rate_reconstructed"),("AorticRoot","luminal_area"),
        ("Radial","flow_rate_reconstructed"),("Radial","luminal_area"),
        ("Femoral","pressure"),("Femoral","flow_rate_reconstructed"),("Femoral","luminal_area")]
    used={("Radial","pressure"),("Carotid","luminal_area"),("Carotid","pressure"),("Carotid","flow_rate_reconstructed"),*m3}
    rem=[]
    for site in COMMON_SITES:
        for q in ("pressure","flow_rate_reconstructed","luminal_area"):
            if (site,q) not in used: rem.append((site,q))
    return {"M1":[("Carotid","luminal_area")],
            "M2":[("Carotid","pressure"),("Carotid","flow_rate_reconstructed")],
            "M3":m3,"M4":rem}

def load_component(pws,site,q,counts):
    if q=="pressure": return load_waveform_matrix(pws,site,"P",counts)[0],"pressure"
    if q=="luminal_area": return load_waveform_matrix(pws,site,"A",counts)[0],"luminal_area"
    if q=="flow_rate_reconstructed": return load_flow_rate_matrix(pws,site,counts),"flow_rate_reconstructed"
    raise AssertionError(q)

def information_geometry(w,d,a,xi):
    out={}
    zero=np.zeros(6,dtype=np.int8)
    for age in AGES:
        mask=a==age
        base=np.flatnonzero(mask & np.all(xi==zero,axis=1))
        req(len(base)==1,f"baseline state missing age {age}")
        stencil={}
        for k,f in enumerate(FACTOR_ORDER):
            minus=zero.copy(); plus=zero.copy(); minus[k]=-1; plus[k]=1
            im=np.flatnonzero(mask & np.all(xi==minus,axis=1)); ip=np.flatnonzero(mask & np.all(xi==plus,axis=1))
            req(len(im)==len(ip)==1,f"stencil missing {age} {f}")
            stencil[f]=(w[im[0]],d[im[0]],w[ip[0]],d[ip[0]])
        g=local_information_metric(stencil)
        out[str(age)]={"eigenvalues":g["eigenvalues"].tolist(),"eigenvectors":g["eigenvectors"].tolist(),
                       "condition_number":g["condition_number"],"weakest_direction":g["weakest_direction"].tolist()}
    return out

def numerical_audit(w,d,a,primary_best,primary_target):
    audit=set()
    for age in AGES:
        ids=np.flatnonzero(a==age)
        for k in np.linspace(0,len(ids)-1,10,dtype=int): audit.add(int(ids[k]))
    audit.update(np.flatnonzero(np.abs(primary_best-1.0)<=0.01).tolist())
    rows=[]; maxdiff=0.0
    for s in sorted(audit):
        cand=np.flatnonzero(a!=a[s])
        diff=w[cand].astype(np.float64)-w[s].astype(np.float64)
        dp=np.sqrt(np.mean(diff*diff,axis=1))
        dt=np.abs(d[cand]-d[s])
        dist=np.sqrt((dp/5.0)**2+(dt/10.0)**2)
        mn=float(dist.min()); choices=cand[dist<=mn+TIE_ATOL]; targ=int(choices.min())
        delta=abs(mn-float(primary_best[s])); maxdiff=max(maxdiff,delta)
        req(delta<=1e-4,f"float audit D_ref disagreement subject {s+1}: {delta}")
        req((mn<=1.0)==(primary_best[s]<=1.0),f"float audit alias class disagreement subject {s+1}")
        rows.append({"subject_id":s+1,"primary_D_ref":float(primary_best[s]),"float64_D_ref":mn,
                     "abs_difference":delta,"primary_target_id":int(primary_target[s])+1,"float64_target_id":targ+1})
    return {"subjects_audited":len(rows),"max_abs_D_ref_difference":maxdiff,"rows":rows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--execute-locked-trial",action="store_true")
    ap.add_argument("--expected-lock-package-sha",required=True)
    ap.add_argument("--repo-root",required=True); ap.add_argument("--pwdb-root",required=True); ap.add_argument("--output-root",required=True)
    args=ap.parse_args()
    req(args.execute_locked_trial,"biological endpoint execution requires --execute-locked-trial")
    repo=Path(args.repo_root).resolve(); pwdb=Path(args.pwdb_root).resolve(); out=Path(args.output_root).resolve(); out.mkdir(parents=True,exist_ok=True)
    manifest=validate_lock(repo,args.expected_lock_package_sha)
    cfg=json.loads((repo/"phase3"/"LOCKED_TRIAL_CONFIG.json").read_text())
    req(cfg["biological_endpoints_allowed_in_phase3"] is False,"lock config corrupted")
    pws=pwdb/"PWs_csv.zip"; var=pwdb/"pwdb_model_variations.csv"; haem=pwdb/"pwdb_haemod_params.csv"
    for p in (pws,var,haem): req(p.exists(),f"missing source {p.name}")
    ages,xi=load_variations(var)
    radial,counts=load_waveform_matrix(pws,"Radial","P")
    durations=duration_vector_from_counts(counts)

    i,j,dp,dt=all_pair_components_jax(radial,durations,ages)
    req(len(i)==7971615,"cross-age pair count drift")
    np.savez_compressed(out/"primary_pair_components.npz",i=i,j=j,pressure_rmse_mmHg=dp,duration_diff_ms=dt)
    dref=reference_pair_distance(dp,dt); best,target,ties=canonical_nearest_from_pairs(4374,i,j,dref)
    ref_pair=dref<=1.0; ref_subject=subject_alias_exists(4374,i,j,ref_pair)
    surface=alias_surface(i,j,dp,dt)
    write_csv(out/"primary_tolerance_surface.csv",["pressure_tolerance_mmHg","duration_tolerance_ms","alias_pairs","subjects_with_alias","alias_fraction"],
              [{"pressure_tolerance_mmHg":ep,"duration_tolerance_ms":et,"alias_pairs":p,"subjects_with_alias":s,"alias_fraction":f} for ep,et,p,s,f in surface])
    ap_rows=primary_age_pair_rows(ages,i,j,ref_pair)
    write_csv(out/"primary_age_pair_matrix.csv",list(ap_rows[0]),ap_rows)
    subj=[]
    for s in range(4374):
        row={"subject_id":s+1,"age":int(ages[s]),**{f:int(xi[s,k]) for k,f in enumerate(FACTOR_ORDER)},
             "D_ref":float(best[s]),"nearest_subject_id":int(target[s])+1,"nearest_age":int(ages[target[s]]),
             "tie_count":int(ties[s]),"reference_alias":bool(best[s]<=1.0)}
        subj.append(row)
    write_csv(out/"primary_subject_results.csv",list(subj[0]),subj)

    # Replication P1/P2
    ppg,_=load_waveform_matrix(pws,"Digital","PPG",counts)
    ppgd=selected_chunked(ppg,i,j,"ppg_shape")
    ppg_ref=np.sqrt((ppgd/0.20)**2+(dt/10.0)**2)<=1.0
    carotid,_=load_waveform_matrix(pws,"Carotid","P",counts)
    cdp=selected_chunked(carotid,i,j,"pressure")
    carotid_ref=np.sqrt((cdp/5.0)**2+(dt/10.0)**2)<=1.0
    rep=[{"arm":"P0_Radial_pressure","pair_aliases":int(ref_pair.sum()),"subject_alias_fraction":float(ref_subject.mean())},
         {"arm":"P1_Digital_PPG","pair_aliases":int(ppg_ref.sum()),"subject_alias_fraction":float(subject_alias_exists(4374,i,j,ppg_ref).mean())},
         {"arm":"P2_Carotid_pressure","pair_aliases":int(carotid_ref.sum()),"subject_alias_fraction":float(subject_alias_exists(4374,i,j,carotid_ref).mean())}]
    write_csv(out/"replication_summary.csv",list(rep[0]),rep)
    del ppg,ppgd,carotid,cdp

    # Mechanistic compensation
    src=np.flatnonzero(best<=1.0).astype(np.int32); tgt=target[src]
    vec=compensation_vectors(xi,src,tgt)
    comp_rows=[]
    for n,s in enumerate(src):
        comp_rows.append({"subject_id":int(s)+1,"source_age":int(ages[s]),"target_subject_id":int(tgt[n])+1,"target_age":int(ages[tgt[n]]),
                          **{f"delta_{f}":int(vec[n,k]) for k,f in enumerate(FACTOR_ORDER)}})
    write_csv(out/"compensation_vectors.csv",list(comp_rows[0]) if comp_rows else ["subject_id"],comp_rows)
    motif_obs=top_k_motif_concentration(vec,20) if len(vec) else 0.0
    if len(src):
        null=compensation_null(src,ages[tgt],ages,xi,permutations=int(cfg["compensation"]["null_permutations"]),seed=int(cfg["compensation"]["random_seed"]),k=20)
        null95=float(np.quantile(null,0.95))
    else:
        null=np.array([],dtype=float); null95=0.0
    json.dump({"top20_observed":motif_obs,"null_95th":null95,"permutations":len(null),
               "S4_no_go":bool(len(src)>0 and motif_obs<=null95)},(out/"compensation_null_summary.json").open("w"),indent=2)
    if len(vec):
        uniq,cnt=np.unique(vec,axis=0,return_counts=True); order=np.argsort(cnt)[::-1]
        motifs=[{**{f"delta_{f}":int(uniq[q,k]) for k,f in enumerate(FACTOR_ORDER)},"count":int(cnt[q]),"fraction":float(cnt[q]/len(vec))} for q in order]
        write_csv(out/"compensation_motifs.csv",list(motifs[0]),motifs)
    else:
        (out/"compensation_motifs.csv").write_text("")

    # Nested measurement rescue
    survivor=ref_pair.copy(); rescue_rows=[]; increments=incremental_rescue_components()
    for arm in ("M1","M2","M3","M4"):
        for site,q in increments[arm]:
            pos=np.flatnonzero(survivor)
            if len(pos)==0: break
            mat,mode=load_component(pws,site,q,counts)
            dist=selected_chunked(mat,i[pos],j[pos],mode); del mat
            threshold=5.0 if mode=="pressure" else 0.05
            survivor[pos] &= dist<=threshold
        rf=rescue_fraction_by_subject(4374,i,j,ref_pair,survivor)
        rescue_rows.append({"arm":arm,"surviving_pair_aliases":int(survivor.sum()),
                            "subjects_with_alias":int(subject_alias_exists(4374,i,j,survivor).sum()),
                            "rescue_fraction_among_P0_alias_subjects":rf})
    write_csv(out/"measurement_rescue_summary.csv",list(rescue_rows[0]),rescue_rows)

    # Conventional benchmark
    pwv=load_scalar_column(haem,"PWV_a [m/s]"); aix=load_scalar_column(haem,"AIx [%]"); sbp=load_scalar_column(haem,"SBP_b [mmHg]")
    denom=np.maximum(np.abs(pwv[i])+np.abs(pwv[j]),1e-12)
    pwv_rel=2.0*np.abs(pwv[i]-pwv[j])/denom
    pwv_alias=pwv_rel<=0.05
    comp_alias=pwv_alias & (np.abs(aix[i]-aix[j])<=5.0) & (np.abs(sbp[i]-sbp[j])<=5.0)
    pair_j=jaccard_bool(ref_pair,pwv_alias)
    subj_pwv=subject_alias_exists(4374,i,j,pwv_alias); subj_agree=float(np.mean(subj_pwv==ref_subject))
    conventional={"pwv_only_pair_alias_jaccard_with_P0":pair_j,"pwv_only_subject_alias_agreement":subj_agree,
                  "pwv_only_alias_fraction":float(subj_pwv.mean()),
                  "composite_alias_fraction":float(subject_alias_exists(4374,i,j,comp_alias).mean()),
                  "S5_downgrade":bool(pair_j>=0.90 and subj_agree>=0.95)}
    json.dump(conventional,(out/"conventional_benchmark.json").open("w"),indent=2)

    # Local information geometry and numerical audit
    json.dump(information_geometry(radial,durations,ages,xi),(out/"information_geometry.json").open("w"),indent=2)
    audit=numerical_audit(radial,durations,ages,best,target); json.dump(audit,(out/"numerical_audit.json").open("w"),indent=2)

    morphology_only=subject_alias_exists(4374,i,j,dp<=5.0)
    surface_fracs=[r[-1] for r in surface]
    flags={
      "S1_no_go":bool(all(f<0.01 for f in surface_fracs)),
      "S3_no_go":bool(ref_subject.mean()<0.01 and ref_subject.mean()<0.20*morphology_only.mean()),
      "S4_no_go":bool(len(src)>0 and motif_obs<=null95),
      "S5_downgrade":conventional["S5_downgrade"],
      "S6_no_go":bool(all(r["rescue_fraction_among_P0_alias_subjects"]<0.10 for r in rescue_rows)),
      "S2_deferred_to_phase5":True
    }
    summary={"phase":4,"status":"EXECUTED","lock_package_sha256":args.expected_lock_package_sha,
             "phase3_parent_main_commit":cfg["parent_main_commit"],"vascuquest_commit":cfg["dataset"]["vascuquest_commit"],
             "subjects":4374,"unordered_cross_age_pairs":len(i),"P0_reference_alias_fraction":float(ref_subject.mean()),
             "P0_reference_alias_pairs":int(ref_pair.sum()),"falsification_flags":flags}
    json.dump(summary,(out/"trial_summary.json").open("w"),indent=2)
    prov={"lock_manifest":manifest,"argv":sys.argv,"python":sys.version,"numpy":np.__version__,
          "jax_backend":__import__("jax").default_backend(),"environment":{"JAX_ENABLE_X64":os.environ.get("JAX_ENABLE_X64")}}
    json.dump(prov,(out/"execution_provenance.json").open("w"),indent=2)
    print(json.dumps(summary,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
