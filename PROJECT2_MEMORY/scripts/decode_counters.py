import argparse, atexit, tempfile, zipfile, csv, json, struct, collections, statistics
from pathlib import Path
from dissect.etl import ETL

parser = argparse.ArgumentParser(description='Decode the three-counter WPR kernel study. Requires dissect.etl==3.14.')
parser.add_argument('session_archive', type=Path)
parser.add_argument('trace_archive', type=Path)
parser.add_argument('--output', type=Path, default=Path('processed-kernel'))
args = parser.parse_args()
workdir = tempfile.TemporaryDirectory(prefix='memory-counters-')
atexit.register(workdir.cleanup)
root = Path(workdir.name)
for archive in [args.session_archive, args.trace_archive]:
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            destination = (root/item.filename).resolve()
            assert destination.is_relative_to(root.resolve()), 'Unsafe archive path'
            z.extract(item, root)
out = args.output
out.mkdir(parents=True, exist_ok=True)
def readtext(p):
    b=p.read_bytes()
    return b.decode('utf-16') if b.startswith((b'\xff\xfe',b'\xfe\xff')) else b.decode('utf-8-sig')
trials=[]
for p in sorted(root.glob('n*_run*.csv')):
    a=list(csv.DictReader(readtext(p).splitlines()))
    assert len(a)==1, p
    a=a[0]
    assert a['correctness']=='PASS'
    for k in ['pid','tid','cpu','n','working_set_bytes','repetitions','qpc_frequency','qpc_start','qpc_end']:
        a[k]=int(a[k])
    for k in ['total_seconds','ns_per_element','gflops','checksum']: a[k]=float(a[k])
    a['run']=int(p.stem.split('_run')[1])
    assert a['working_set_bytes']==12*a['n']
    seconds=(a['qpc_end']-a['qpc_start'])/a['qpc_frequency']
    work=a['n']*a['repetitions']
    assert abs(seconds-a['total_seconds'])<1e-8
    assert abs(seconds*1e9/work-a['ns_per_element'])<0.00000051
    assert abs(work/seconds/1e9-a['gflops'])<0.00000051
    trials.append(a)
assert len(trials)==20
assert {(t['n'],t['run']) for t in trials}=={(n,r) for n in [1024,16384,262144,8388608] for r in range(1,6)}
print('power before:',readtext(root/'power_before.txt').strip())
print('power after:',readtext(root/'power_after.txt').strip())
print('hashes:',readtext(root/'hashes.txt'))
rows=[];configs=[];missing=[]
with (root/'kernel_study.etl').open('rb') as f:
    etl=ETL(f)
    hdr=etl.logfile_header._header
    assert hdr.EventsLost==0 and hdr.BufferLost==0
    frequency=etl.logfile_header.perf_freq
    for b in etl.buffers():
        d=b.data;off=0;cpu=b.header.ProcessorIndex
        while off+8<=len(d):
            marker=struct.unpack_from('<I',d,off)[0];ht=(marker>>16)&255
            sz=struct.unpack_from('<H',d,off+4 if ht in [1,2,3,4,16,17,18,19] else off)[0]
            if sz<8: break
            assert off+sz<=len(d)
            rec=d[off:off+sz]
            if ht==17:
                hook=struct.unpack_from('<H',rec,6)[0]
                if hook==0x524:
                    if (marker&0x700)!=0x300:
                        missing.append((cpu,struct.unpack_from('<Q',rec,8)[0]));off+=(sz+7)&~7;continue
                    ts=struct.unpack_from('<Q',rec,8)[0]
                    ct=struct.unpack_from('<3Q',rec,16)
                    new,old=struct.unpack_from('<II',rec,40)
                    rows.append((cpu,ts,new,old,*ct))
                elif hook==0xf30:
                    p=bytes(b.read_record(off).header.payload)
                    if 'LLCMisses'.encode('utf-16-le') in p:
                        count=struct.unpack_from('<I',p)[0]
                        names=p[4:].decode('utf-16-le').strip('\0').split('\0')
                        assert count==3 and len(names)==3
                        configs.append(names)
            off+=(sz+7)&~7
assert configs and all(x==configs[0] for x in configs)
assert not any(a['qpc_start'] <= ts <= a['qpc_end'] for cpu,ts in missing for a in trials), 'Missing PMCs in a timed window'
print('CSwitch without PMCs:',len(missing),'timestamp range:',(min(ts for _,ts in missing),max(ts for _,ts in missing)) if missing else None)
names=configs[0]
assert set(names)=={'InstructionRetired','LLCMisses','TotalCycles'}
rows.sort(key=lambda r:(r[0],r[1]))
last={};bytid=collections.defaultdict(list)
for cpu,ts,new,old,*ct in rows:
    if cpu in last:
        pts,pnew,pct=last[cpu]
        assert pnew==old, 'Thread continuity failure'
        delta=[a-b for a,b in zip(ct,pct)]
        assert min(delta)>=0, 'Negative counter delta'
        bytid[old].append((cpu,pts,ts,delta))
    last[cpu]=(ts,new,ct)
for a in trials:
    assert a['qpc_frequency']==frequency
    start,end=a['qpc_start'],a['qpc_end'];work=a['n']*a['repetitions']
    intervals=[v for v in bytid[a['tid']] if v[1]<end and v[2]>start]
    inside=[v for v in intervals if v[1]>=start and v[2]<=end]
    assert inside and all(v[0]==0 for v in intervals)
    a['contained_intervals']=len(inside)
    a['boundary_intervals']=len(intervals)-len(inside)
    a['contained_on_cpu_seconds']=sum(v[2]-v[1] for v in inside)/frequency
    for i,name in enumerate(names):
        lower=sum(v[3][i] for v in inside)
        upper=sum(v[3][i] for v in intervals)
        a[name+'_lower']=lower
        a[name+'_upper']=upper
        a[name+'_per_element_lower']=lower/work
        a[name+'_per_element_upper']=upper/work
    # Bounds avoid prorating counters across QPC measurement boundaries.
with (out/'kernel_counters.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(trials[0]));writer.writeheader();writer.writerows(trials)
summary=[]
for n in [1024,16384,262144,8388608]:
    group=[t for t in trials if t['n']==n]
    s={'n':n,'working_set_bytes':12*n,'trials':5}
    for key in ['ns_per_element','gflops','LLCMisses_per_element_lower','LLCMisses_per_element_upper','TotalCycles_per_element_lower','TotalCycles_per_element_upper']:
        for label,fn in [('median',statistics.median),('min',min),('max',max)]:
            s[key+'_'+label]=fn(t[key] for t in group)
    summary.append(s)
print('metadata order',names,'CSwitch records',len(rows))
print(json.dumps(summary,indent=2))
(out/'kernel_counter_summary.json').write_text(json.dumps({'counter_order':names,'context_switch_records':len(rows),'events_lost':0,'buffers_lost':0,'summary':summary},indent=2))
