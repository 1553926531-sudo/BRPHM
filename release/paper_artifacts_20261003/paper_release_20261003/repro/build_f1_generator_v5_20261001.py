#!/usr/bin/env python3
from __future__ import annotations
import csv, pathlib, re, shutil, sys

def main() -> int:
    root=pathlib.Path(sys.argv[1]).resolve(); source=pathlib.Path(sys.argv[2]).resolve(); gen=pathlib.Path(sys.argv[3]).resolve()
    if gen.exists(): raise FileExistsError(gen)
    shutil.copytree(source,gen,symlinks=True)
    all_rows=list(csv.DictReader((root/'sim/logs/manifest.csv').open(newline='',encoding='utf-8')))
    rows=[]
    for index, orbit in enumerate(('LEO500','LEO550','LEO700'),1):
        cand=[r for r in all_rows if r['line']=='bat' and r['orbit']==orbit and r['fault_inject']=='none']
        cand.sort(key=lambda r:(float(r['overrides_aging_scale']) if 'overrides_aging_scale' in r else float(r['est_tf_days']),r['sample_id']),reverse=True)
        # Use the registered high-aging DOE card for this orbit; no semantic labels are read.
        cand=[r for r in all_rows if r['line']=='bat' and r['orbit']==orbit and r['fault_inject']=='none']
        cand.sort(key=lambda r:(float(r['est_tf_days']),r['sample_id']))
        row=cand[0]
        new_id=re.sub(r'_S\d{3}$',f'_S{995+index:03d}',row['sample_id'])
        text=(root/row['yaml']).read_text(encoding='utf-8')
        text=re.sub(r'^sample_id: .*?$',f'sample_id: {new_id}',text,flags=re.M)
        text=re.sub(r'^seed: .*?$',f'seed: {740000+index}',text,flags=re.M)
        text=re.sub(r'^stop_time_max_s: .*?$', 'stop_time_max_s: 401800',text,flags=re.M)
        text=re.sub(r'^est_tf_days: .*?$', 'est_tf_days: 4.65',text,flags=re.M)
        (gen/'configs_sim'/'sample'/f'{new_id}.yaml').write_text(text,encoding='utf-8')
        out=dict(row); out.update(sample_id=new_id,yaml=f'configs/sim/sample/{new_id}.yaml',out_mat=f'data/raw/sim/bat/{new_id}.mat',seed=str(740000+index),stop_time_s='401800',est_tf_days='4.65',queue_order=str(index)); rows.append(out)
    manifest=gen/'sim/logs/manifest.csv'
    with manifest.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=list(all_rows[0])); w.writeheader(); w.writerows(rows)
    print([(r['sample_id'],r['orbit'],r['stop_time_s'],r['est_tf_days']) for r in rows])
    return 0
if __name__=='__main__': raise SystemExit(main())
