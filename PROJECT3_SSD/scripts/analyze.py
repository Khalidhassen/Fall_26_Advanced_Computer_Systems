"""Rebuild parsed tables, validation, and figures from the preserved fio JSON files."""
from pathlib import Path
import csv, hashlib, itertools, json, statistics, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; DATA=ROOT/'data/processed'; PLOTS=ROOT/'plots'
DATA.mkdir(parents=True,exist_ok=True); PLOTS.mkdir(exist_ok=True)
EXPECTED={
 'baseline':{f'{rw}_{bs}_run{r}' for rw,bs in [('randread','4k'),('randwrite','4k'),('seqread','128k'),('seqwrite','128k')] for r in range(1,4)},
 'blocks':{f'{rw}_{bs}_run{r}' for rw,bs,r in itertools.product(['randread','randwrite','read','write'],['4k','16k','32k','64k','128k','256k'],range(1,4))},
 'qd-read':{f'randread_4k_qd{q}_run{r}' for q,r in itertools.product([1,2,4,8,16,32,64,128,256],range(1,4))},
 'mix':{f'read{m}_write{100-m}_run{r}' for m,r in itertools.product([100,70,50,0],range(1,4))},
 'range':{f'range_{s}_run{r}' for s,r in itertools.product(['64M','256M','2G'],range(1,4))},
 'cache-pitfall':{f'{m}_run{r}' for m,r in itertools.product(['direct','buffered'],range(1,4))},
 'write-series':{f'write_series_run{r}' for r in range(1,4)}}
errors=[]; notes=[]; jobs=[]; rows=[]; depth_rows=[]; states=[]
for entry in json.loads((RAW/'manifest.json').read_text()):
 p=ROOT/entry['path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:errors.append(f'Hash mismatch: {p}')

def size_bytes(s):
 s=str(s).lower();return int(s[:-1])*{'k':1024,'m':1024**2,'g':1024**3}[s[-1]] if s[-1] in 'kmg' else int(s)

def check(ok,message):
 if not ok:errors.append(message)

for folder in sorted(p for p in RAW.iterdir() if p.is_dir()):
 for path in sorted(folder.glob('*.json')):
  d=json.loads(path.read_text(encoding='utf-8-sig'))
  if path.name.startswith('state_'):
   states.append({'study':folder.name,'file':path.name,**d});continue
  if 'jobs' not in d:continue
  check(len(d['jobs'])==1,f'{path.name}: job count')
  j=d['jobs'][0];o={**d.get('global options',{}),**j.get('job options',{})}
  study=folder.name; trial=path.stem;warm=trial.startswith('warmup_');main=study in EXPECTED and not warm
  check(j['error']==0,f'{study}/{trial}: fio error')
  for direction in ['read','write']:
   a=j[direction];check(a['short_ios']==0 and a['drop_ios']==0,f'{study}/{trial}: short/drop')
  if main:
   for k,v in {'ioengine':'windowsaio','numjobs':'1','allow_file_create':'0'}.items():check(str(o.get(k))==v,f'{study}/{trial}: {k}')
   check(o['filename']=='fio-pilot-20261024-225410.bin',f'{study}/{trial}: target')
   check(o['direct']==('0' if study=='cache-pitfall' and trial.startswith('buffered') else '1'),f'{study}/{trial}: direct')
   expected_q=32 if study in ['mix','range'] else int(trial.split('_qd')[1].split('_')[0]) if study=='qd-read' else 1
   check(int(o['iodepth'])==expected_q,f'{study}/{trial}: QD')
   if study=='blocks':
    rw,bs,_=trial.split('_');check(o['rw']==rw and o['bs']==bs,f'{study}/{trial}: block condition')
   if study=='mix':
    m=int(trial.split('_')[0][4:]);check(int(o['rwmixread'])==m,f'{trial}: mix')
    check(o['rw']==({100:'randread',0:'randwrite'}.get(m,'randrw')),f'{trial}: direction')
   if study=='range':check(o['size']==trial.split('_')[1],f'{trial}: range')
   if study=='cache-pitfall':check(o['invalidate']=='0' and o['size']=='256M',f'{trial}: cache setup')
   if study=='write-series':check(o['io_size']=='40G' and o['time_based']=='0' and o['runtime']=='120',f'{trial}: cap')
   if study not in ['blocks','baseline']:check(o['bs']==('128k' if study=='write-series' else '4k'),f'{trial}: block size')
   if study not in ['range','cache-pitfall']:check(o['size']=='2G',f'{trial}: range size')
   if study not in ['baseline','blocks','mix','write-series']:check(o['rw']=='randread',f'{trial}: read pattern')
   if study!='write-series':check(o['runtime']=='20' and o['ramp_time']=='3',f'{trial}: timing')
  if warm:check(j['read']['io_bytes']==256*1024**2 and o['direct']=='0',f'{trial}: warmup')
  if o['rw'] in ['read','randread']:check(j['write']['io_bytes']==0,f'{trial}: unintended writes')
  if o['rw'] in ['write','randwrite'] and not (study=='pilot' and trial=='prepare'):check(j['read']['io_bytes']==0,f'{trial}: unintended reads')
  total_ios=sum(j[k]['total_ios'] for k in ['read','write']);total_bw=sum(j[k]['bw_bytes'] for k in ['read','write'])/1e6
  record={'study':study,'trial':trial,'main':main,'warmup':warm,'rw':o['rw'],'bs_bytes':size_bytes(o['bs']),'range_bytes':size_bytes(o['size']),'requested_qd':int(o['iodepth']),'direct':int(o['direct']),'read_percent_requested':int(o.get('rwmixread',100 if 'read' in o['rw'] else 0)),'read_percent_observed':100*j['read']['total_ios']/total_ios,'total_MB_s':total_bw,'total_iops':sum(j[k]['iops'] for k in ['read','write'])}
  jobs.append(record)
  delta_sum=0
  for direction in ['read','write']:
   a=j[direction]
   if not a['total_ios']:continue
   lat=a['lat_ns'];pct=lat.get('percentile',{});delta=a['io_bytes']-a['total_ios']*record['bs_bytes'];delta_sum+=delta
   check(abs(a['iops']-a['total_ios']*1000/a['runtime'])<1e-5,f'{trial}: IOPS arithmetic')
   check(abs(a['bw_bytes']-a['io_bytes']*1000/a['runtime'])<1.1,f'{trial}: bandwidth arithmetic')
   if main and study!='write-series':check(a['runtime']>=20000,f'{trial}: short measurement')
   if main and study=='write-series':check(a['io_bytes']<=40*1024**3,f'{trial}: byte cap')
   row={**record,'direction':direction,'runtime_s':a['runtime']/1000,'io_bytes':a['io_bytes'],'total_ios':a['total_ios'],'byte_minus_ios_bytes':delta,'MB_s':a['bw_bytes']/1e6,'iops':a['iops'],'mean_us':lat['mean']/1000,'p50_us':pct.get('50.000000',math.nan)/1000,'p95_us':pct.get('95.000000',math.nan)/1000,'p99_us':pct.get('99.000000',math.nan)/1000,'p999_us':pct.get('99.900000',math.nan)/1000,'estimated_outstanding_total':a['iops']*lat['mean']/1e9}
   rows.append(row)
  if delta_sum:notes.append(f'{study}/{trial}: bytes exceed counted operations by {delta_sum} bytes; retained, not corrected.')
  if main:check(0<=delta_sum<=record['requested_qd']*record['bs_bytes'],f'{trial}: byte-count discrepancy beyond QD bound')
  for bucket,value in j['iodepth_level'].items():depth_rows.append({'study':study,'trial':trial,'requested_qd':record['requested_qd'],'bucket':bucket,'percent':value})
for study,expected in EXPECTED.items():
 found={j['trial'] for j in jobs if j['study']==study and j['main']}
 check(found==expected,f'{study}: missing {sorted(expected-found)}, unexpected {sorted(found-expected)}')
for p in RAW.glob('*/power_*.txt'):check('(Performance)' in p.read_text(encoding='utf-8-sig'),f'{p}: power plan')

def write_csv(name,data):
 fields=list(dict.fromkeys(k for r in data for k in r))
 with (DATA/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
write_csv('trials.csv',rows);write_csv('jobs.csv',jobs);write_csv('depth_distributions.csv',depth_rows);write_csv('device_states.csv',states)
summary=[]
keys=['study','rw','bs_bytes','range_bytes','requested_qd','direct','read_percent_requested','direction']
metrics=['MB_s','iops','mean_us','p50_us','p95_us','p99_us','p999_us','estimated_outstanding_total']
groups={}
for r in rows:
 if r['main']:groups.setdefault(tuple(r[k] for k in keys),[]).append(r)
for key,rs in groups.items():
 s=dict(zip(keys,key));s['repeats']=len(rs)
 for m in metrics:
  vals=[r[m] for r in rs];s[m+'_median']=statistics.median(vals);s[m+'_min']=min(vals);s[m+'_max']=max(vals)
 summary.append(s)
write_csv('summary.csv',summary)
validation={'errors':errors,'status':'PASS' if not errors else 'FAIL','main_measurements':sum(j['main'] for j in jobs),'all_fio_jobs':len(jobs),'preserved_raw_files':len(json.loads((RAW/'manifest.json').read_text())),'notes':notes,'note':'PASS means coverage/settings/arithmetic/recorded fio status passed, not independent verification of all written data.'}
(DATA/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
if errors:raise SystemExit('\n'.join(errors))

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
COLORS=['#1768AC','#D45C27','#238773','#8864AF']
def select(study,**filters):return [r for r in rows if r['main'] and r['study']==study and all(r[k]==v for k,v in filters.items())]
def med(rs,key):return statistics.median(r[key] for r in rs)
def errorpoint(ax,x,rs,key,**kwargs):
 vals=[r[key] for r in rs];v=statistics.median(vals);ax.errorbar(x,v,yerr=[[v-min(vals)],[max(vals)-v]],capsize=3,**kwargs)
def finish(fig,name,caption):
 fig.text(.5,.012,caption,ha='center',fontsize=8);fig.tight_layout(rect=(0,.05,1,1))
 for ext in ['png','svg']:fig.savefig(PLOTS/(name+'.'+ext))
 plt.close(fig)
labels=['Random read\n4 KiB','Random write\n4 KiB','Sequential read\n128 KiB','Sequential write\n128 KiB']
conds=[('randread',4096),('randwrite',4096),('read',131072),('write',131072)]
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
for i,(rw,bs) in enumerate(conds):
 rs=select('baseline',rw=rw,bs_bytes=bs);errorpoint(axs[0],i,rs,'mean_us',fmt='o',color=COLORS[i])
 for off,key in zip([-.2,-.07,.07,.2],['p50_us','p95_us','p99_us','p999_us']):errorpoint(axs[1],i+off,rs,key,fmt='o',color=COLORS[['p50_us','p95_us','p99_us','p999_us'].index(key)],label=key.replace('_us','') if i==0 else None)
for ax in axs:ax.set_xticks(range(4),labels);ax.set_yscale('log');ax.set_ylabel('Total latency (µs)');ax.grid(axis='y',alpha=.2)
axs[0].set_title('QD1 baseline: mean latency');axs[1].set_title('QD1 baseline: latency percentiles');axs[1].legend()
finish(fig,'baseline','Original baseline session only. Points: medians of 3 trials; bars: trial minimum–maximum (not confidence intervals).')
fig,axs=plt.subplots(1,2,figsize=(12,4.6));sizes=[4096,16384,32768,65536,131072,262144]
for c,rw in zip(COLORS,['randread','randwrite','read','write']):
 for ax,key in zip(axs,['MB_s','mean_us']):
  ys=[]
  for bs in sizes:
   rs=select('blocks',rw=rw,bs_bytes=bs);ys.append(med(rs,key));errorpoint(ax,bs/1024,rs,key,fmt='o',color=c)
  ax.plot([s/1024 for s in sizes],ys,color=c,label=rw)
for ax in axs:ax.set_xscale('log',base=2);ax.set_xlabel('Block size (KiB)');ax.set_xticks([4,16,32,64,128,256],[4,16,32,64,128,256]);ax.grid(alpha=.2)
axs[0].set_ylabel('Throughput (decimal MB/s)');axs[1].set_ylabel('Mean total latency (µs)');axs[1].set_yscale('log');axs[0].legend();axs[0].set_title('Block-size throughput');axs[1].set_title('Latency from the same trials')
finish(fig,'blocks','QD1, one job, direct I/O, 2 GiB range. Median and minimum–maximum across 3 trials per condition.')
qd=[1,2,4,8,16,32,64,128,256]
fig,ax=plt.subplots(figsize=(7.8,5))
xs=[];ys=[]
for q in qd:
 rs=select('qd-read',requested_qd=q);x=med(rs,'mean_us');y=med(rs,'MB_s');xs.append(x);ys.append(y)
 ax.scatter([r['mean_us'] for r in rs],[r['MB_s'] for r in rs],s=16,alpha=.35,color=COLORS[0])
 ax.errorbar(x,y,xerr=[[x-min(r['mean_us'] for r in rs)],[max(r['mean_us'] for r in rs)-x]],yerr=[[y-min(r['MB_s'] for r in rs)],[max(r['MB_s'] for r in rs)-y]],fmt='o',capsize=3,color=COLORS[0]);ax.annotate(str(q),(x,y),xytext=(5,6),textcoords='offset points')
ax.plot(xs,ys,color=COLORS[0],alpha=.5);ax.set_xlabel('Mean total latency (µs)');ax.set_ylabel('Throughput (decimal MB/s)');ax.set_title('Random-read throughput–latency tradeoff');ax.grid(alpha=.2)
finish(fig,'qd_curve','4 KiB, direct I/O, one job, 2 GiB. Labels: requested QD. Faint points: individual trials; bars: trial range.')
fig,ax=plt.subplots(figsize=(7.8,4.8))
for c,key,label in zip(COLORS,['mean_us','p95_us','p99_us','p999_us'],['Mean','p95','p99','p99.9']):
 ys=[]
 for q in qd:
  rs=select('qd-read',requested_qd=q);ys.append(med(rs,key));errorpoint(ax,q,rs,key,fmt='o',color=c)
 ax.plot(qd,ys,label=label,color=c)
ax.set_xscale('log',base=2);ax.set_yscale('log');ax.set_xlabel('Requested queue depth');ax.set_ylabel('Total latency (µs)');ax.set_title('Random-read tails increase beyond the knee');ax.legend();ax.grid(alpha=.2)
finish(fig,'qd_tails','Same QD trials as throughput curve. Medians of per-trial statistics, not pooled percentiles; bars show trial range.')
fig,ax=plt.subplots(figsize=(7.8,4.8))
for q in qd:errorpoint(ax,q,select('qd-read',requested_qd=q),'estimated_outstanding_total',fmt='o',color=COLORS[0])
ax.plot(qd,qd,'--',color='gray',label='Requested depth');ax.set_xscale('log',base=2);ax.set_yscale('log');ax.set_xlabel('Requested queue depth');ax.set_ylabel('Estimated average outstanding I/O');ax.set_title('Little’s Law: IOPS × mean total latency');ax.legend();ax.grid(alpha=.2)
finish(fig,'little_law','Estimate calculated per trial, then summarized. fio-level estimate is not measured NVMe controller occupancy.')
fig,axs=plt.subplots(1,2,figsize=(11,4.7));mixes=[100,70,50,0]
for i,m in enumerate(mixes):
 js=[j for j in jobs if j['study']=='mix' and j['read_percent_requested']==m];errorpoint(axs[0],i,js,'total_MB_s',fmt='o',color=COLORS[0])
 for direction,c,off in [('read',COLORS[0],-.08),('write',COLORS[1],.08)]:
  rs=select('mix',read_percent_requested=m,direction=direction)
  if rs:errorpoint(axs[1],i+off,rs,'p99_us',fmt='o',color=c,label=direction if (direction=='read' and i==0) or (direction=='write' and i==1) else None)
for ax in axs:ax.set_xticks(range(4),['100/0','70/30','50/50','0/100']);ax.set_xlabel('Requested read/write mix (%)');ax.grid(axis='y',alpha=.2)
axs[0].set_ylabel('Total throughput (decimal MB/s)');axs[1].set_ylabel('p99 total latency (µs)');axs[0].set_title('Mix throughput');axs[1].set_title('Read and write tails');axs[1].legend()
finish(fig,'mix','4 KiB random I/O, requested QD32, one job, direct I/O, 2 GiB. Median and trial range, 3 repeats.')
for study,values,filterkey,labels,title in [('range',[64*2**20,256*2**20,2*2**30],'range_bytes',['64 MiB','256 MiB','2 GiB'],'Accessed file range'),('cache-pitfall',[1,0],'direct',['Direct','Buffered'],'Buffered-read measurement pitfall')]:
 fig,axs=plt.subplots(1,2,figsize=(10,4.5))
 for i,v in enumerate(values):
  rs=select(study,**{filterkey:v});errorpoint(axs[0],i,rs,'MB_s',fmt='o',color=COLORS[0]);errorpoint(axs[1],i,rs,'mean_us',fmt='o',color=COLORS[1])
 for ax in axs:ax.set_xticks(range(len(values)),labels);ax.grid(axis='y',alpha=.2)
 axs[0].set_ylabel('Throughput (decimal MB/s)');axs[1].set_ylabel('Mean total latency (µs)');fig.suptitle(title)
 finish(fig,'range' if study=='range' else 'cache_pitfall','4 KiB random reads, one job. '+('Direct I/O, requested QD32.' if study=='range' else 'QD1, 256 MiB; each trial preceded by a buffered read warm-up.')+' Median and range, 3 repeats.')
series=[];fig,axs=plt.subplots(2,1,figsize=(11,7),sharex=True)
for r,c in zip(range(1,4),COLORS):
 for kind,ax,factor in [('bw',axs[0],1024/1e6),('lat',axs[1],1e-6)]:
  p=next((RAW/'write-series').glob(f'*run{r}_{kind}.1.log'));raw=list(csv.reader(p.open()));ts=[float(x[0])/1000 for x in raw];vs=[float(x[1])*factor for x in raw]
  ax.plot(ts,vs,label=f'Run {r}',color=c,linewidth=1.3)
  for x in raw:series.append({'run':r,'kind':kind,'time_s':float(x[0])/1000,'value_raw':float(x[1]),'direction':int(x[2]),'display_value':float(x[1])*factor,'display_unit':'MB/s' if kind=='bw' else 'ms'})
axs[0].set_ylabel('Throughput (decimal MB/s)');axs[1].set_ylabel('Window mean total latency (ms)');axs[1].set_yscale('log');axs[1].set_xlabel('Time from run start (s)');axs[0].set_title('Bounded sequential write time series: all repeats')
for ax in axs:ax.legend();ax.grid(alpha=.2)
finish(fig,'write_series','128 KiB, QD1, direct I/O, 2 GiB range; stop at 40 GiB or 120 s. One-second averages; final intervals may be partial.')
write_csv('write_series.csv',series)
print(f'PASS: {validation["main_measurements"]} main measurements, {len(jobs)} total fio jobs, {len(notes)} bounded byte-count notes. Wrote 9 figures (PNG + SVG).')
