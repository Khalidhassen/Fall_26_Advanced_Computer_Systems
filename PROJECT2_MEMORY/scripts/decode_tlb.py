"""Audit a TLB-counter collection attempt from its original Windows ZIP.
The submitted study failed TLB validation; its zero readings are diagnostic only.
Requires dissect.etl==3.14. Thread IDs come from ETL initial-thread start records,
matched to command arguments and each CSV's QPC window; they are not guessed.
"""
import argparse, collections, csv, hashlib, json, re, statistics, struct, tempfile, zipfile
from pathlib import Path
from dissect.etl import ETL


def readtext(p):
    b=p.read_bytes()
    return b.decode('utf-16') if b.startswith((b'\xff\xfe',b'\xfe\xff')) else b.decode('utf-8-sig')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--output',type=Path,default=Path('data/processed'))
    parser.add_argument('--allow-zero-response',action='store_true',help='Export a failed diagnostic explicitly; never label its zero readings as measured misses.')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='memory-tlb-') as folder:
        work=Path(folder)
        with zipfile.ZipFile(args.archive) as z:
            assert z.testzip() is None
            for item in z.infolist():
                p=Path(item.filename.replace('\\','/'))
                assert not p.is_absolute() and '..' not in p.parts
                if not item.is_dir():
                    dest=work/p;dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes(z.read(item))
        etls=list(work.rglob('tlb_study.etl'));assert len(etls)==1
        base=etls[0].parent
        for name in ['power_before.txt','power_after.txt']:
            s=readtext(base/name)
            assert 'Performance' in s and '27fa6203-3987-4dcc-918d-748559d549ec' in s
        trials=[]
        for p in sorted(base.glob('n*_s*_run*.csv')):
            a=list(csv.DictReader(readtext(p).splitlines()));assert len(a)==1
            a=a[0];assert a['correctness']=='PASS' and a['mode']=='normal'
            for k in ['cpu','nodes','spacing_bytes','unique_cacheline_bytes','span_bytes','allocated_bytes','page_bytes','loads','seed','qpc_frequency','qpc_start','qpc_end']:a[k]=int(a[k])
            for k in ['total_seconds','ns_per_load']:a[k]=float(a[k])
            a['run']=int(re.search(r'_run(\d+)',p.stem)[1]);a['file']=p.name
            assert a['loads']==100000000 and a['page_bytes']==4096 and a['cpu']==0 and a['seed']==2477034263
            assert a['unique_cacheline_bytes']==a['nodes']*64 and a['span_bytes']==a['nodes']*a['spacing_bytes']
            assert a['allocated_bytes']>=a['span_bytes'] and a['allocated_bytes']%4096==0
            elapsed=(a['qpc_end']-a['qpc_start'])/a['qpc_frequency']
            assert abs(elapsed-a['total_seconds'])<1e-8
            assert abs(elapsed*1e9/a['loads']-a['ns_per_load'])<0.00000051
            trials.append(a)
        expected={(n,s,r) for n in [32,128,512,2048,8192] for s in [64,4096] for r in range(1,6)}
        assert len(trials)==50 and {(a['nodes'],a['spacing_bytes'],a['run']) for a in trials}==expected
        rows=[];configs=[];missing=[];processes={};thread_starts=[]
        with etls[0].open('rb') as f:
            etl=ETL(f);hdr=etl.logfile_header._header
            assert hdr.EventsLost==0 and hdr.BufferLost==0
            frequency=etl.logfile_header.perf_freq
            for b in etl.buffers():
                d=b.data;off=0;cpu=b.header.ProcessorIndex
                while off+8<=len(d):
                    marker=struct.unpack_from('<I',d,off)[0];ht=(marker>>16)&255
                    size=struct.unpack_from('<H',d,off+4 if ht in [1,2,3,4,16,17,18,19] else off)[0]
                    if size<8:break
                    assert off+size<=len(d)
                    rec=d[off:off+size]
                    hook=struct.unpack_from('<H',rec,6)[0] if ht in [1,2,3,4,16,17,18,19] else -1
                    if ht==17 and hook==0x524:
                        ts=struct.unpack_from('<Q',rec,8)[0]
                        if (marker&0x700)!=0x300:missing.append((cpu,ts))
                        else:
                            counts=struct.unpack_from('<3Q',rec,16)
                            new,old=struct.unpack_from('<II',rec,40)
                            rows.append((cpu,ts,new,old,*counts))
                    elif ht==17 and hook==0xf30:
                        payload=bytes(b.read_record(off).header.payload)
                        count=struct.unpack_from('<I',payload)[0]
                        names=payload[4:].decode('utf-16-le').strip('\0').split('\0')
                        assert count==3 and len(names)==3
                        configs.append(names)
                    elif ht==2 and hook==0x501:
                        record=b.read_record(off);payload=bytes(record.header.payload)
                        assert record.header.version==3
                        pid,tid=struct.unpack_from('<II',payload)
                        thread_starts.append(dict(pid=pid,tid=tid,start=struct.unpack_from('<Q',rec,16)[0],creator_pid=record.header.process_id))
                    elif ht==2 and hook in [0x301,0x302]:
                        record=b.read_record(off);payload=bytes(record.header.payload)
                        image=b'page_chase.exe\0'
                        if image in payload:
                            assert record.header.version==4
                            pid=struct.unpack_from('<I',payload,8)[0]
                            command=payload.split(image,1)[1].decode('utf-16-le').rstrip('\0')
                            m=re.search(r'"\s+(\d+)\s+(\d+)\s+(\d+)\s+(normal|large)\b',command)
                            assert m,command
                            proc=processes.setdefault(pid,{'pid':pid,'args':m.groups(),'parent_pid':struct.unpack_from('<I',payload,12)[0]})
                            assert proc['args']==m.groups()
                            ts=struct.unpack_from('<Q',rec,16)[0]
                            key='start' if hook==0x301 else 'end'
                            assert key not in proc,'Process ID reused during study'
                            proc[key]=ts
                            if hook==0x302:
                                assert record.header.process_id==pid
                                proc['exit_tid']=record.header.thread_id
                    off+=(size+7)&~7
        assert configs and all(c==configs[0] for c in configs)
        names=configs[0]
        assert set(names)=={'InstructionRetired','TotalCycles','KH_ADL_RETIRED_STLB_MISS'}
        assert not any(a['qpc_start']<=ts<=a['qpc_end'] for cpu,ts in missing for a in trials)
        rows.sort(key=lambda r:(r[0],r[1]))
        last={};bytid=collections.defaultdict(list)
        for cpu,ts,new,old,*counts in rows:
            if cpu in last:
                pts,pnew,previous=last[cpu]
                assert pnew==old,'Thread continuity failure'
                delta=[a-b for a,b in zip(counts,previous)]
                assert min(delta)>=0,'Negative counter delta'
                bytid[old].append((cpu,pts,ts,delta))
            last[cpu]=(ts,new,counts)
        for a in trials:
            start,end=a['qpc_start'],a['qpc_end']
            assert a['qpc_frequency']==frequency
            command=(str(a['nodes']),str(a['spacing_bytes']),str(a['loads']),'normal')
            candidates=[p for p in processes.values() if p['args']==command and p.get('start',float('inf'))<=start and p.get('end',0)>=end]
            assert len(candidates)==1,(a['file'],candidates)
            proc=candidates[0];a['pid']=proc['pid']
            initial=[t for t in thread_starts if t['pid']==proc['pid'] and t['creator_pid']==proc['parent_pid'] and proc['start']<=t['start']<=start]
            assert len(initial)==1,(a['file'],initial)
            a['tid']=initial[0]['tid']
            intervals=[v for v in bytid[a['tid']] if v[1]<end and v[2]>start]
            assert intervals and all(v[0]==0 for v in intervals),('Timed thread migrated off CPU 0',a['file'],a['pid'],a['tid'],sorted({v[0] for v in intervals}),proc)
            inside=[v for v in intervals if v[1]>=start and v[2]<=end]
            assert inside
            a['contained_intervals']=len(inside);a['boundary_intervals']=len(intervals)-len(inside)
            a['contained_on_cpu_seconds']=sum(v[2]-v[1] for v in inside)/frequency
            for i,name in enumerate(names):
                lower=sum(v[3][i] for v in inside);upper=sum(v[3][i] for v in intervals)
                a[name+'_lower']=lower;a[name+'_upper']=upper
                a[name+'_per_load_lower']=lower/a['loads'];a[name+'_per_load_upper']=upper/a['loads']
            assert a['InstructionRetired_lower']>0 and a['TotalCycles_lower']>0
        responsive=any(a['KH_ADL_RETIRED_STLB_MISS_lower']>0 for a in trials)
        if not responsive and not args.allow_zero_response:
            raise ValueError('TLB event did not respond in any timed window; rejected as TLB evidence')
        for a in trials:a['tlb_counter_usable']=responsive
        out=args.output;out.mkdir(parents=True,exist_ok=True)
        with (out/'tlb_attempt_trials.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(trials[0]));writer.writeheader();writer.writerows(trials)
        summary=[]
        for n in [32,128,512,2048,8192]:
            for s in [64,4096]:
                g=[a for a in trials if a['nodes']==n and a['spacing_bytes']==s]
                a=dict(nodes=n,spacing_bytes=s,trials=len(g))
                for metric in ['ns_per_load','KH_ADL_RETIRED_STLB_MISS_per_load_lower','KH_ADL_RETIRED_STLB_MISS_per_load_upper']:
                    for label,fn in [('median',statistics.median),('minimum',min),('maximum',max)]:a[metric+'_'+label]=fn(r[metric] for r in g)
                summary.append(a)
        audit=dict(status='PASS' if responsive else 'TLB_ZERO_RESPONSE',tlb_counter_usable=responsive,trials=len(trials),counter_order=names,context_switch_records=len(rows),startup_switches_without_pmcs=len(missing),events_lost=0,buffers_lost=0,thread_mapping='ETL process command lines/lifetimes and initial-thread start records; parent-created thread verified against timed CSV QPC window',normalization='known timed dependent-load count; not the unsupported all-retired-load counter',archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(),etl_sha256=hashlib.sha256(etls[0].read_bytes()).hexdigest(),summary=summary)
        (out/'tlb_attempt_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
