#!/usr/bin/env python3
"""Reproduce all summaries and plots from preserved user measurements."""
from pathlib import Path
import csv,re,json,statistics as st
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; OUT=ROOT/'processed'; PLOT=ROOT/'plots'
OUT.mkdir(exist_ok=True); PLOT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150,'savefig.bbox':'tight'})
COL=['#155e75','#d97706','#7c3aed']
def write(name,rows):
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def read(name):
 with (RAW/name).open() as f:return list(csv.DictReader(f))
def stats(values):
 return {'median':st.median(values),'min':min(values),'max':max(values),'q1':float(np.percentile(values,25)),'q3':float(np.percentile(values,75)),'samples':len(values)}
def save(fig,name):
 fig.tight_layout();fig.savefig(PLOT/(name+'.png'));fig.savefig(PLOT/(name+'.pdf'));plt.close(fig)
# Initial sweeps: parse actual printed size/repetitions and reject mislabeled groups.
baseline=[]
for kernel,name in [('multiply','multiply_results_corrected.txt'),('axpy','axpy_results.txt'),('dot','dot_results.txt')]:
 text=(RAW/name).read_text()
 pattern=r'Configuration: (\d+) (\d+) \| Run: (\d+) \| (scalar|SIMD)\s+(.*?)(?=Configuration:|\Z)'
 for m in re.finditer(pattern,text,re.S):
  label_n,label_rep,run,build,body=m.groups()
  n=int(re.search(r'Elements: (\d+)',body)[1]);rep=int(re.search(r'Repetitions: (\d+)',body)[1])
  assert n==int(label_n) and rep==int(label_rep)
  assert 'Correctness: PASS' in body
  seconds=float(re.search(r'Total time: ([\d.]+)',body)[1]); flops=1 if kernel=='multiply' else 2
  baseline.append(dict(kernel=kernel,build=build.lower(),run=int(run),n=n,repetitions=rep,total_seconds=seconds,us_per_pass=seconds/rep*1e6,gflops=flops*n*rep/seconds/1e9,ns_per_element=seconds/rep/n*1e9,working_set_bytes=n*(12 if kernel=='multiply' else 8)))
 assert sum(r['kernel']==kernel for r in baseline)==24
write('baseline_runs.csv',baseline)
summaries=[]; groups=defaultdict(list)
for r in baseline:groups[r['kernel'],r['n'],r['build']].append(r)
for (k,n,b),rs in sorted(groups.items()):
 s=stats([r['us_per_pass'] for r in rs]);summary=dict(kernel=k,n=n,build=b,working_set_bytes=rs[0]['working_set_bytes'],**{'us_'+key:v for key,v in s.items()});summary['gflops_median']=st.median(r['gflops'] for r in rs);summary['ns_per_element']=s['median']*1000/n; summary['hardware_cycles_per_element']='unavailable';summaries.append(summary)
write('baseline_summary.csv',summaries)
speed=[]
for k,n in sorted(set((r['kernel'],r['n']) for r in baseline)):
 s=stats([r['us_per_pass'] for r in groups[k,n,'scalar']]);v=stats([r['us_per_pass'] for r in groups[k,n,'simd']]);speed.append(dict(kernel=k,n=n,speedup=s['median']/v['median']))
write('baseline_speedup.csv',speed)
fig,axs=plt.subplots(1,2,figsize=(10.8,4))
for j,k in enumerate(['multiply','axpy','dot']):
 rs=[r for r in speed if r['kernel']==k];axs[0].plot([r['n'] for r in rs],[r['speedup'] for r in rs],'o-',label=k,color=COL[j])
 for b,ls in [('scalar','--'),('simd','-')]:
  rr=sorted([r for r in summaries if r['kernel']==k and r['build']==b],key=lambda r:r['n']); xx=[r['n'] for r in rr]; yy=[r['gflops_median'] for r in rr]
  lo=[];hi=[]
  for r,y in zip(rr,yy):
   vals=[a['gflops'] for a in groups[k,r['n'],b]];lo.append(y-min(vals));hi.append(max(vals)-y)
  axs[1].errorbar(xx,yy,yerr=[lo,hi],fmt='o'+ls,color=COL[j],capsize=3,label=k+' '+b)
for ax in axs:ax.set_xscale('log',base=2);ax.set_xlabel('Elements per array');ax.grid(alpha=.2)
axs[0].axhline(1,color='gray',ls=':');axs[0].set_ylabel('Median scalar / median SIMD time');axs[0].legend();axs[0].set_title('Initial sweeps: speedup')
axs[1].set_ylabel('GFLOP/s');axs[1].set_title('Throughput: median and min-max');axs[1].legend(fontsize=7,ncol=2)
save(fig,'01_baseline')
# CSV experiments: recompute metrics from elapsed time rather than rounded output.
checks={}; experiments={}
for name,keys,metric in [('layout',['build','n','offset_bytes'],'ns_per_element'),('stride',['build','length','stride'],'ns_per_element'),('types',['dtype','build','n'],'us_per_pass')]:
 rows=read(name+'_results.csv'); expected={'layout':160,'stride':80,'types':120}[name];assert len(rows)==expected
 gg=defaultdict(list)
 for r in rows:
  assert r['correctness']=='PASS'; t=float(r['total_seconds']);rep=int(r['repetitions']);n=int(r.get('n',r.get('processed')))
  r['value']=t/rep*(1e6 if metric=='us_per_pass' else 1e9/n)
  gg[tuple(r[key] for key in keys)].append(r)
 ss=[]
 for key,rr in sorted(gg.items()):
  assert len(rr)==5
  ss.append(dict(zip(keys,key),metric=metric,**stats([r['value'] for r in rr])))
 write(name+'_summary.csv',ss);experiments[name]=(gg,ss);checks[name]=len(rows)
# Alignment: normalize to useful elements, not passes.
fig,axs=plt.subplots(1,2,figsize=(10.8,3.6))
for offset,color in [('0',COL[0]),('4',COL[1])]:
 for ax,b in zip(axs,['scalar','simd']):
  rr=sorted([r for r in experiments['layout'][1] if r['build']==b and r['offset_bytes']==offset],key=lambda r:int(r['n']));y=np.array([r['median'] for r in rr]);ax.errorbar([int(r['n'])%8 for r in rr],y,yerr=[y-[r['min'] for r in rr],[r['max'] for r in rr]-y],fmt='o-',capsize=3,color=color,label=offset+' byte offset');ax.set_title(b);ax.set_xlabel('Remainder N mod 8 (N = 1024...1031)');ax.set_ylabel('ns / processed element');ax.legend();ax.grid(alpha=.2)
save(fig,'02_alignment_tail')
fig,axs=plt.subplots(1,2,figsize=(10.8,3.6))
for ax,length in zip(axs,['1024','8388608']):
 for b,color in [('scalar',COL[0]),('auto',COL[1])]:
  rr=sorted([r for r in experiments['stride'][1] if r['build']==b and r['length']==length],key=lambda r:int(r['stride']));y=np.array([r['median'] for r in rr]);ax.errorbar([int(r['stride']) for r in rr],y,yerr=[y-[r['min'] for r in rr],[r['max'] for r in rr]-y],fmt='o-',capsize=3,label=b,color=color)
 ax.set_title('12 KiB arrays' if length=='1024' else '96 MiB arrays');ax.set_xlabel('Stride');ax.set_ylabel('ns / processed element');ax.set_xticks([1,2,4,8]);ax.legend();ax.grid(alpha=.2)
save(fig,'03_stride')
fig,axs=plt.subplots(1,2,figsize=(10.8,3.8))
for ax,dtype in zip(axs,['float','double']):
 for b,color in zip(['scalar','default','native'],COL):
  rr=sorted([r for r in experiments['types'][1] if r['dtype']==dtype and r['build']==b],key=lambda r:int(r['n']));y=np.array([int(r['n'])/r['median']/1000 for r in rr]);lo=y-np.array([int(r['n'])/r['max']/1000 for r in rr]);hi=np.array([int(r['n'])/r['min']/1000 for r in rr])-y
  ax.errorbar([int(r['n']) for r in rr],y,yerr=[lo,hi],fmt='o-',capsize=3,label=b,color=color)
 ax.set_xscale('log',base=2);ax.set_title(dtype+' multiplication');ax.set_xlabel('Elements per array');ax.set_ylabel('GFLOP/s');ax.legend();ax.grid(alpha=.2)
save(fig,'04_types_builds')
bw=read('bandwidth_results.csv');assert len(bw)==5 and all(r['correctness']=='PASS' for r in bw)
useful=[2*int(r['n'])*4*int(r['repetitions'])/float(r['total_seconds'])/2**30 for r in bw]; modeled=[x*1.5 for x in useful];B=st.median(modeled)*2**30/1e9
# Explicit hypothetical P-core peaks; not measured clock or core placement.
roof=dict(useful_gib_s=stats(useful),modeled_gib_s=stats(modeled),modeled_GB_s=B,assumed_Pcore_GHz=4.7,SP_FMA_peak_GFLOPs=150.4,DP_FMA_peak_GFLOPs=75.2,SP_multiply_peak_GFLOPs=75.2,DP_multiply_peak_GFLOPs=37.6,SP_AI=1/16,DP_AI=1/32,SP_memory_reference_GFLOPs=B/16,DP_memory_reference_GFLOPs=B/32)
(OUT/'roofline_assumptions.json').write_text(json.dumps(roof,indent=2))
fig,ax=plt.subplots(figsize=(9,4.2));intens=np.logspace(-2,2,300)
for dtype,peak,color in [('float',150.4,COL[0]),('double',75.2,COL[1])]:
 ax.loglog(intens,np.minimum(B*intens,peak),color=color,label=dtype+' P-core FMA roof (assumed 4.7 GHz)')
 ai=1/(16 if dtype=='float' else 32);r=next(r for r in experiments['types'][1] if r['dtype']==dtype and r['build']=='native' and r['n']=='8388608');g=8388608/r['median']/1000
 ax.scatter([ai],[g],color=color,s=65,zorder=5);ax.annotate(dtype+' multiply',xy=(ai,g),xytext=(9,12 if dtype=='float' else -18),textcoords='offset points',fontsize=8)
ax.fill_between(intens,np.minimum(min(modeled)*2**30/1e9*intens,150.4),np.minimum(max(modeled)*2**30/1e9*intens,150.4),color='gray',alpha=.12,label='Copy-run bandwidth range (SP roof)')
ax.set_xlabel('Arithmetic intensity (FLOP / modeled DRAM byte)');ax.set_ylabel('GFLOP/s');ax.set_title('Illustrative single-P-core roofline; actual frequency/core unknown');ax.grid(which='both',alpha=.2);ax.legend(fontsize=8,loc='lower right');save(fig,'05_roofline')
checks.update(baseline=len(baseline),bandwidth=len(bw),total=72+160+80+120+5,all_correctness_pass=True)
(OUT/'validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks));print(json.dumps(roof,indent=2))
