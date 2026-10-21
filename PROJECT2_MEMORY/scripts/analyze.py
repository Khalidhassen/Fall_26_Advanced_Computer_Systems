"""Rebuild processed tables and publication figures from archived raw logs.
Run from anywhere: python scripts/analyze.py
PMCs: rerun scripts/decode_counters.py first to independently decode the ETL.
"""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json, math, re, statistics, zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, FIG = ROOT/'data/raw', ROOT/'data/processed', ROOT/'plots'
OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(exist_ok=True)

def text(b):
    if b.startswith((b'\xff\xfe', b'\xfe\xff')): return b.decode('utf-16')
    try: return b.decode('utf-8-sig')
    except UnicodeDecodeError: return b.decode('cp1252')

def write_csv(name, rows):
    assert rows, name
    with (OUT/name).open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def stats(values):
    v=list(values)
    return dict(median=statistics.median(v), minimum=min(v), maximum=max(v), trials=len(v))

archives={}
for p in sorted(RAW.glob('*.zip')):
    with zipfile.ZipFile(p) as z:
        archives[p.stem]={name:z.read(name) for name in z.namelist() if not name.endswith('/')}

def session(prefix):
    names=[n for n in archives if n.startswith(prefix)]
    assert len(names)==1, (prefix,names)
    return names[0]

mlc=[]; failures=[]; native=[]
for name, files in archives.items():
    if name=='original-hypotheses': continue
    plans=[text(b) for fn,b in files.items() if 'power' in fn and fn.endswith('.txt')]
    power='Performance recorded before/after' if any('before' in fn and 'Performance' in text(b) for fn,b in files.items()) and any('after' in fn and 'Performance' in text(b) for fn,b in files.items()) else 'Not bracketed by session power logs'
    for fn,b in files.items():
        if fn.endswith('.csv'):
            a=list(csv.DictReader(text(b).splitlines())); assert len(a)==1, (name,fn)
            a=a[0]
            assert a['correctness']=='PASS', (name,fn)
            a['session']=name; a['file']=fn
            m=re.search(r'_run(\d+)', fn); a['run']=int(m[1]) if m else 0
            native.append(a)
        if not fn.endswith('.txt'): continue
        s=text(b)
        cmd=re.search(r'^Command line parameters: (.*)$',s,re.M)
        latency=re.search(r'Each iteration took\s+([\d.]+) base frequency clocks\s*\(\s*([\d.]+)\s+ns\)',s)
        loaded=re.findall(r'^[ \t]*(\d{5})[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]*\r?$',s,re.M)
        if 'Assertion failed' in s or 'Exiting..' in s or 'Unable to enable' in s:
            failures.append(dict(session=name,file=fn,detail='4 KiB fallback' if 'using 4k pages' in s else 'No valid result / allocation or command error'))
        if not latency and not loaded: continue
        assert cmd, (name,fn)
        c=cmd[1].strip()
        def option(flag,default=''):
            m=re.search(r'(?:^| )'+re.escape(flag)+r'([\d,]+)(?: |$)',c)
            return int(m[1]) if m and m[1].isdigit() else default
        stride=option('-l',128 if re.search(r'(?:^| )-r(?: |$)',c) else 64)
        m=re.search(r'_run(\d+)',fn);run=int(m[1]) if m else 0
        mix='read-only'
        if '-W3' in c: mix='75/25'
        elif '-W5' in c: mix='50/50'
        elif '-W6' in c: mix='NT writes'
        pattern='random' if '-U' in c or re.search(r'(?:^| )-r(?: |$)',c) else 'sequential'
        base=dict(session=name,file=fn,run=run,buffer_kib=option('-b'),stride_bytes=stride,pattern=pattern,mix=mix,command=c,power_evidence=power,latency_measured='-T' not in c,role='main' if '_run' in fn and not name.startswith('kernel-pilot') else 'pilot',fallback_4k='using 4k pages' in s)
        if latency:
            mlc.append(dict(**base,delay='',latency_ns=float(latency[2]),bandwidth_MB_s='',base_clocks=float(latency[1])))
        for d,l,bw in loaded:
            mlc.append(dict(**base,delay=int(d),latency_ns=float(l) if '-T' not in c else '',bandwidth_MB_s=float(bw),base_clocks=''))

# Exact condition/run coverage for the completed main studies.
expected={
 'cache-sweep-':70,'cache-128B-':70,'spacing-check-':10,
 'loaded-latency-':50,'loaded-performance-':50,'pattern-bandwidth-':30,
 'pattern-latency-':30,'rw-mixes-':20,'read-bandwidth-':5,'mixed-latency-':20,
 '20261020-080651':5,
}
for prefix,count in expected.items():
    subset=[r for r in mlc if r['session']==session(prefix)]
    assert len(subset)==count,(prefix,len(subset))
    keys=[(r['file'],r['delay']) for r in subset]; assert len(set(keys))==count
for prefix in ['cache-sweep-','cache-128B-']:
    sub=[r for r in mlc if r['session']==session(prefix)]
    assert {(r['buffer_kib'],r['run']) for r in sub}=={(n,i) for n in [16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072] for i in range(1,6)}
for prefix in ['pattern-latency-','pattern-bandwidth-']:
    sub=[r for r in mlc if r['session']==session(prefix)]
    assert {(r['stride_bytes'],r['pattern'],r['run']) for r in sub}=={(s,p,i) for s in [64,256,1024] for p in ['sequential','random'] for i in range(1,6)}
for prefix in ['loaded-latency-','loaded-performance-']:
    sub=[r for r in mlc if r['session']==session(prefix)]
    assert {(r['delay'],r['run']) for r in sub}=={(d,i) for d in [30000,10000,3200,1600,800,400,200,100,50,0] for i in range(1,6)}
for prefix in ['mixed-latency-','rw-mixes-']:
    sub=[r for r in mlc if r['session']==session(prefix)]
    assert {(r['mix'],r['run']) for r in sub}=={(m,i) for m in ['read-only','75/25','50/50','NT writes'] for i in range(1,6)}
write_csv('mlc_trials.csv',mlc)
write_csv('failed_or_fallback_runs.csv',failures)

kernel=[];pages=[];cache=[]
for a in native:
    for k in ['qpc_frequency','qpc_start','qpc_end']: a[k]=int(a[k])
    elapsed=(a['qpc_end']-a['qpc_start'])/a['qpc_frequency']
    assert abs(elapsed-float(a['total_seconds']))<1e-8
    if 'n' in a:
        for k in ['n','repetitions','working_set_bytes','tid','pid','cpu']:a[k]=int(a[k])
        work=a['n']*a['repetitions']; assert a['working_set_bytes']==a['n']*12
        assert abs(elapsed*1e9/work-float(a['ns_per_element']))<0.00000051
        assert abs(work/elapsed/1e9-float(a['gflops']))<0.00000051
        period=sum((i%100)*.25*(i%50)*.5 for i in range(100))
        checksum=(a['n']//100)*period+sum((i%100)*.25*(i%50)*.5 for i in range(a['n']%100))
        assert math.isclose(float(a['checksum']),checksum,rel_tol=1e-8)
        if a['session'].startswith('kernel-study-'):kernel.append(a)
    else:
        for k in ['nodes','spacing_bytes','page_bytes','loads','seed','cpu','unique_cacheline_bytes','span_bytes','allocated_bytes']:a[k]=int(a[k])
        assert a['mode']=='normal' and a['page_bytes']==4096 and a['cpu']==0
        assert a['seed']==2477034263
        assert a['allocated_bytes']>=a['span_bytes'] and a['allocated_bytes']%4096==0
        assert a['unique_cacheline_bytes']==a['nodes']*64
        assert a['span_bytes']==a['nodes']*a['spacing_bytes']
        assert abs(elapsed*1e9/a['loads']-float(a['ns_per_load']))<0.00000051
        if a['session'].startswith('cache-latency-'):
            assert a['spacing_bytes']==64
            assert a['loads']==(100000000 if a['nodes']<=65536 else 20000000)
            cache.append(a)
        else:
            assert a['session'].startswith('page-locality-') and a['loads']==100000000
            pages.append(a)
assert len(kernel)==20 and {(a['n'],a['run']) for a in kernel}=={(n,i) for n in [1024,16384,262144,8388608] for i in range(1,6)}
assert len(pages)==50 and {(a['nodes'],a['spacing_bytes'],a['run']) for a in pages}=={(n,s,i) for n in [32,128,512,2048,8192] for s in [64,4096] for i in range(1,6)}
write_csv('kernel_trials.csv',kernel);write_csv('page_locality_trials.csv',pages)

cache_nodes=[512,4096,16384,65536,262144,524288,2097152]
assert len(cache)==35 and {(a['nodes'],a['run']) for a in cache}=={(n,i) for n in cache_nodes for i in range(1,6)}
cache_files=archives[session('cache-latency-')]
for fn in ['power_before.txt','power_after.txt']:
    assert '27fa6203-3987-4dcc-918d-748559d549ec' in text(cache_files[fn]) and 'Performance' in text(cache_files[fn])
cache_hashes=text(cache_files['hashes.txt']).lower()
assert hashlib.sha256((ROOT/'src/cache_latency.c').read_bytes()).hexdigest() in cache_hashes
write_csv('cache_latency_trials.csv',cache)
cache_summary=[]
for n in cache_nodes:
    a=dict(nodes=n,active_bytes=n*64,active_kib=n/16)
    a.update({'ns_per_load_'+k:v for k,v in stats(float(r['ns_per_load']) for r in cache if r['nodes']==n).items()})
    cache_summary.append(a)
write_csv('cache_latency_summary.csv',cache_summary)

# A counter-validation failure does not invalidate separately checked timings.
# These diagnostic zeros are never interpreted as zero TLB misses.
with (OUT/'tlb_attempt_trials.csv').open(newline='') as f:followup=list(csv.DictReader(f))
tlb_audit=json.loads((OUT/'tlb_attempt_audit.json').read_text())
assert tlb_audit['status']=='TLB_ZERO_RESPONSE' and tlb_audit['tlb_counter_usable'] is False
assert tlb_audit['trials']==50 and tlb_audit['events_lost']==tlb_audit['buffers_lost']==0
attempt_archive=RAW/'counter-attempts/tlb-study.zip'
assert hashlib.sha256(attempt_archive.read_bytes()).hexdigest()==tlb_audit['archive_sha256']
with zipfile.ZipFile(attempt_archive) as z:
    raw_followup={Path(n.replace('\\','/')).name:b for n in z.namelist() if n.endswith('.csv') for b in [z.read(n)]}
for a in followup:
    raw_row=list(csv.DictReader(text(raw_followup[a['file']]).splitlines()))[0]
    for k,v in raw_row.items():
        if k in ['total_seconds','ns_per_load']:assert float(v)==float(a[k])
        else:assert str(v)==str(a[k])
    for k in ['nodes','spacing_bytes','run','loads','qpc_frequency','qpc_start','qpc_end']:a[k]=int(a[k])
    assert a['correctness']=='PASS' and a['tlb_counter_usable']=='False'
    assert int(a['KH_ADL_RETIRED_STLB_MISS_lower'])==int(a['KH_ADL_RETIRED_STLB_MISS_upper'])==0
    elapsed=(a['qpc_end']-a['qpc_start'])/a['qpc_frequency']
    assert abs(elapsed-float(a['total_seconds']))<1e-8
    assert abs(elapsed*1e9/a['loads']-float(a['ns_per_load']))<0.00000051
assert len(followup)==50 and {(a['nodes'],a['spacing_bytes'],a['run']) for a in followup}=={(n,s,i) for n in [32,128,512,2048,8192] for s in [64,4096] for i in range(1,6)}
followup_summary=[]
for n in [32,128,512,2048,8192]:
    for spacing in [64,4096]:
        a=dict(nodes=n,spacing_bytes=spacing,tlb_counter_status='EXCLUDED_ZERO_RESPONSE')
        a.update({'ns_per_load_'+k:v for k,v in stats(float(a['ns_per_load']) for a in followup if a['nodes']==n and a['spacing_bytes']==spacing).items()})
        followup_summary.append(a)
write_csv('page_locality_followup_summary.csv',followup_summary)


with (OUT/'kernel_counters.csv').open(newline='') as f:counters=list(csv.DictReader(f))
assert len(counters)==20
for a in kernel:
    match=[r for r in counters if int(r['tid'])==a['tid'] and int(r['qpc_start'])==a['qpc_start']]
    assert len(match)==1
    for k in ['qpc_end','n','repetitions']:assert int(match[0][k])==a[k]

groups=defaultdict(list)
for r in mlc:
    groups[(r['session'],r['buffer_kib'],r['stride_bytes'],r['pattern'],r['mix'],r['delay'])].append(r)
summary=[]
for key,g in groups.items():
    a=dict(zip(['session','buffer_kib','stride_bytes','pattern','mix','delay'],key))
    for metric in ['latency_ns','bandwidth_MB_s']:
        v=[r[metric] for r in g if r[metric]!='']
        for k,val in (stats(v).items() if v else {'median':'','minimum':'','maximum':'','trials':0}.items()):a[metric+'_'+k]=val
    summary.append(a)
write_csv('mlc_summary.csv',summary)
def subset(prefix):return [r for r in mlc if r['session']==session(prefix)]
def at(prefix,**kw):return [r for r in subset(prefix) if all(r[k]==v for k,v in kw.items())]

little=[]
for r in subset('loaded-performance-'):
    # Deliberately a scale model, NOT a measured worker concurrency.
    little.append(dict(run=r['run'],delay=r['delay'],bandwidth_GB_s=r['bandwidth_MB_s']/1000,probe_latency_ns=r['latency_ns'],probe_rate_Mloads_s=1000/r['latency_ns'],equivalent_64B_concurrency_model=r['bandwidth_MB_s']*r['latency_ns']/64000))
write_csv('littles_law_model.csv',little)

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white','savefig.facecolor':'white'})
COLORS=['#145c94','#d47a1f','#367a59','#8a477d']
def finish(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(FIG/(name+'.svg'),bbox_inches='tight')
    plt.close(fig)
def error_series(ax,x,groups,label,color,scale=1):
    v=[stats(float(t)/scale for t in g) for g in groups]
    med=np.array([s['median'] for s in v]);lo=np.array([s['minimum'] for s in v]);hi=np.array([s['maximum'] for s in v])
    ax.errorbar(x,med,yerr=[med-lo,hi-med],fmt='o-',capsize=3,label=label,color=color,lw=1.7,markersize=4)
    return med

def bar_groups(ax,groups,color,scale=1):
    v=[stats(float(x)/scale for x in g) for g in groups]
    med=np.array([s['median'] for s in v]);lo=np.array([s['minimum'] for s in v]);hi=np.array([s['maximum'] for s in v])
    ax.bar(range(len(v)),med,color=color,width=.6,yerr=[med-lo,hi-med],capsize=3,error_kw={'ecolor':'#333333','lw':1})

sizes=[16,32,64,128,256,512,1024,2048,4096,8192,16384,32768,65536,131072]
fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
for pref,label,c in [('cache-sweep-','64 B spacing',COLORS[0]),('cache-128B-','128 B spacing',COLORS[1])]:
    error_series(ax,sizes,[[r['latency_ns'] for r in at(pref,buffer_kib=n)] for n in sizes],label,c)
for x,l in [(48,'L1d 48 KiB'),(1024,'L2 display ~1 MiB'),(24576,'LLC 24 MiB')]:
    ax.axvline(x,color='#777777',ls=':',lw=1);ax.text(x,.98,l,rotation=90,va='top',ha='right',fontsize=8,transform=ax.get_xaxis_transform(),bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
ax.set(xscale='log',yscale='log',xlabel='Requested buffer size (KiB)',ylabel='MLC access latency (ns)',title='Working-set sweep: spacing changes the observed curve')
ax.legend(loc='lower right');ax.grid(alpha=.2,which='both')
fig.text(.02,-.045,'Five trials; bars show min–max. Early sessions lack bracketed power records. Cache markers are reference sizes, not fitted transitions.',fontsize=8)
finish(fig,'cache_latency')

fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
x=[n/16 for n in cache_nodes]
error_series(ax,x,[[float(r['ns_per_load']) for r in cache if r['nodes']==n] for n in cache_nodes],'Global random cycle',COLORS[0])
ax.set(xscale='log',yscale='log',xlabel='Active cache-line footprint (KiB)',ylabel='Dependent-load time (ns/load)',title='Global random pointer chain: working-set latency')
ax.set_xticks(x,['32','256','1,024','4,096','16,384','32,768','131,072'])
ax.grid(alpha=.2,which='both')
fig.text(.02,-.045,'CPU 0; normal 4 KiB pages; Performance before/after; five trials, min–max. Includes translation and background effects.',fontsize=8)
finish(fig,'global_random_latency')


fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for p,label,c in [('sequential','Sequential',COLORS[0]),('random','Bounded random',COLORS[1])]:
    for ax,pref,metric,scale in [(axes[0],'pattern-latency-','latency_ns',1),(axes[1],'pattern-bandwidth-','bandwidth_MB_s',1000)]:
        error_series(ax,[64,256,1024],[[r[metric] for r in at(pref,pattern=p,stride_bytes=s)] for s in [64,256,1024]],label,c,scale)
for ax in axes:ax.set_xscale('log',base=2);ax.set_xticks([64,256,1024],['64','256','1,024']);ax.set_xlabel('Spacing (bytes)');ax.grid(alpha=.2)
axes[0].set(ylabel='MLC access latency (ns)',title='Latency — Performance session');axes[1].set(ylabel='MLC estimated bandwidth (GB/s)',title='Bandwidth — earlier session');axes[0].legend()
fig.text(.02,-.045,'Five trials; min–max. Prefetchers left unchanged. Latency and bandwidth are separate workloads/sessions; do not combine them as matched requests.',fontsize=8)
finish(fig,'pattern_sweep')

fig,ax=plt.subplots(figsize=(7.4,4.5),layout='constrained')
delay=[30000,10000,3200,1600,800,400,200,100,50,0]
for run in range(1,6):
    g=sorted([r for r in subset('loaded-performance-') if r['run']==run],key=lambda r:delay.index(r['delay']))
    ax.plot([r['bandwidth_MB_s']/1000 for r in g],[r['latency_ns'] for r in g],color=COLORS[0],alpha=.15,lw=1)
for d in delay:
    g=at('loaded-performance-',delay=d);bs=stats(r['bandwidth_MB_s']/1000 for r in g);ls=stats(r['latency_ns'] for r in g)
    ax.errorbar(bs['median'],ls['median'],xerr=[[bs['median']-bs['minimum']],[bs['maximum']-bs['median']]],yerr=[[ls['median']-ls['minimum']],[ls['maximum']-ls['median']]],fmt='o',color=COLORS[0],capsize=2)
    if d in [30000,400,100,50,0]:ax.annotate('delay '+str(d),(bs['median'],ls['median']),xytext=(4,5),textcoords='offset points',fontsize=8)
ax.set(xlabel='MLC estimated bandwidth (GB/s)',ylabel='Random read-probe latency (ns)',title='Read-only load: latency rises with bandwidth');ax.grid(alpha=.2)
fig.text(.02,-.04,'CPU 0 probe; workers 2,4,6,8,10; Performance plan. Five sweeps; min–max bars. No sharp plateau is established.',fontsize=8)
finish(fig,'loaded_latency')

mixes=['read-only','75/25','50/50','NT writes'];labels=['Read-only','75/25','50/50','NT writes']
fig,axes=plt.subplots(1,2,figsize=(9.2,4),layout='constrained')
for ax,metric,scale in [(axes[0],'latency_ns',1),(axes[1],'bandwidth_MB_s',1000)]:
    g=[at('mixed-latency-',mix=m) for m in mixes]
    bar_groups(ax,[[r[metric] for r in a] for a in g],COLORS[0],scale)
    ax.set_xticks(range(4),labels);ax.grid(axis='y',alpha=.2)
axes[0].set(ylabel='Read-probe latency (ns)',title='Read latency under competing traffic');axes[1].set(ylabel='MLC estimated bandwidth (GB/s)',title='Traffic throughput')
fig.text(.02,-.04,'Five trials, delay 0, five P-core workers. Mixes are MLC traffic presets; NT writes also change the store policy. Error bars: min–max.',fontsize=8)
finish(fig,'mixed_traffic')

fig,ax=plt.subplots(figsize=(7,3.8),layout='constrained')
bar_groups(ax,[[r['bandwidth_MB_s'] for r in at('rw-mixes-',mix=m)] for m in mixes],COLORS[1],1000)
ax.set_xticks(range(4),labels);ax.set(ylabel='MLC estimated bandwidth (GB/s)',title='Earlier single-thread read/write throughput');ax.grid(axis='y',alpha=.2)
fig.text(.02,-.04,'Logical CPU 0; 64 B spacing; throughput-only mode. Session power was not bracketed. Kept separate from the five-worker study.',fontsize=8)
finish(fig,'single_thread_mixes')

fig,axes=plt.subplots(1,3,figsize=(12,3.9),layout='constrained')
ns=[1024,16384,262144,8388608];ks=['12 KiB','192 KiB','3 MiB','96 MiB']
error_series(axes[0],range(4),[[float(r['ns_per_element']) for r in kernel if r['n']==n] for n in ns],'Runtime',COLORS[0])
for ax,prefix,label in [(axes[1],'LLCMisses','LLC misses/element'),(axes[2],'TotalCycles','TotalCycles/element')]:
    low=[];high=[]
    for n in ns:
        g=[r for r in counters if int(r['n'])==n]
        lo=[float(r[prefix+'_per_element_lower']) for r in g];hi=[float(r[prefix+'_per_element_upper']) for r in g]
        low.append(statistics.median(lo));high.append(statistics.median(hi))
        ax.vlines(ns.index(n),min(lo),max(hi),color=COLORS[1],lw=1,alpha=.6)
    ax.fill_between(range(4),low,high,color=COLORS[1],alpha=.25,label='Median boundary range')
    ax.plot(range(4),low,'o-',color=COLORS[1],markersize=4);ax.set_ylabel(label);ax.set_yscale('log')
for ax in axes:ax.set_xticks(range(4),ks,rotation=20);ax.set_xlabel('Three-array working set');ax.grid(axis='y',alpha=.2)
axes[0].set(ylabel='Time (ns/element)',title='Runtime');axes[0].set_yscale('log');axes[1].set_title('LLC-miss counter');axes[2].set_title('Cycle counter')
fig.text(.02,-.055,'Five trials; runtime bars: min–max. Counter bands: median lower/upper attribution bounds; thin lines span trial bounds. Not confidence intervals.',fontsize=8)
finish(fig,'cache_miss_impact')

fig,ax=plt.subplots(figsize=(7.5,4.4),layout='constrained')
nodes=[32,128,512,2048,8192]
for s,label,c in [(64,'Packed: 64 B spacing',COLORS[0]),(4096,'Spread: one node per 4 KiB region',COLORS[1])]:
    error_series(ax,nodes,[[float(r['ns_per_load']) for r in pages if r['nodes']==n and r['spacing_bytes']==s] for n in nodes],label,c)
ax.set(xscale='log',xlabel='Number of nodes (same cache-line count per pair)',ylabel='Dependent-load time (ns/load)',title='Page locality: spread layouts cost more');ax.set_xticks(nodes,[str(n) for n in nodes]);ax.legend();ax.grid(alpha=.2)
fig.text(.02,-.04,'Normal 4 KiB pages only; five trials, min–max. Includes the 9.00 ns packed outlier. Cache effects remain possible; No validated TLB count is assigned to this earlier session.',fontsize=8)
finish(fig,'page_locality')

fig,ax=plt.subplots(figsize=(7.5,4.4),layout='constrained')
for spacing,label,c in [(64,'Packed: 64 B spacing',COLORS[0]),(4096,'Spread: one node per 4 KiB region',COLORS[1])]:
    error_series(ax,nodes,[[float(r['ns_per_load']) for r in followup if r['nodes']==n and r['spacing_bytes']==spacing] for n in nodes],label,c)
ax.set(xscale='log',yscale='log',xlabel='Number of nodes (same cache-line count per pair)',ylabel='Dependent-load time (ns/load)',title='Follow-up locality study: validated timing results')
ax.set_xticks(nodes,[str(n) for n in nodes]);ax.legend();ax.grid(alpha=.2,which='both')
fig.text(.02,-.045,'Separate 50-trial session; CPU 0, Performance, 4 KiB pages; median and min–max. TLB readings failed validation and are excluded.',fontsize=8)
finish(fig,'page_locality_followup')


fig,ax=plt.subplots(figsize=(6.4,4),layout='constrained')
for i,s in enumerate([64,128]):
    v=[r['latency_ns'] for r in at('spacing-check-',stride_bytes=s)]
    med=statistics.median(v);ax.bar(i,med,color=COLORS[i],width=.55)
    ax.errorbar(i,med,yerr=[[med-min(v)],[max(v)-med]],fmt='none',ecolor='#333333',capsize=4)
    ax.scatter([i+(j-2)*.035 for j in range(5)],v,color='#333333',s=15,zorder=3)
ax.set_xticks([0,1],['64 B spacing','128 B spacing']);ax.set(ylabel='MLC random-access latency (ns)',title='Pitfall: spacing changes the answer');ax.grid(axis='y',alpha=.2)
fig.text(.02,-.05,'Same 128 MiB request and D=4096; five paired trials. Spacing also changes random-block byte span. This does not isolate prefetching.',fontsize=8)
finish(fig,'spacing_pitfall')

audit=dict(mlc_measurements=len(mlc),main_mlc_measurements=sum(expected.values()),kernel_trials=len(kernel),page_locality_trials=len(pages),cache_latency_trials=len(cache),page_locality_followup_trials=len(followup),tlb_counter_status=tlb_audit['status'],failed_or_fallback_logs=failures,plots=10,
           counter_input='kernel_counters.csv (regenerate with scripts/decode_counters.py)',
           missing=['Reproducible validated direct TLB-miss counts (attempts retained as negatives)','Successful large-page comparison','Exact 70/30 traffic preset','Definitive physical saturation knee','Per-session power records for early sessions','Measured fixed core frequency'])
(OUT/'validation.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
