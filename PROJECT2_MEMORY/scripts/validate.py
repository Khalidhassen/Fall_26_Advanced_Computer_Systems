"""Integrity and submission checks; run after analyze.py."""
from pathlib import Path
import csv, hashlib, json, re, zipfile
from PIL import Image

root=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
with (root/'docs/RAW_ARCHIVES.csv').open(newline='') as f:raw=list(csv.DictReader(f))
for r in raw:
    p=root/r['path'];assert p.is_file(),p
    assert p.stat().st_size==int(r['bytes']),p
    assert digest(p)==r['sha256'],p
    assert p.stat().st_size < 25*1024*1024,p
    if p.suffix=='.zip':
        with zipfile.ZipFile(p) as z:assert z.testzip() is None,p
provenance=json.loads((root/'docs/BUILD_PROVENANCE.json').read_text())
assert digest(root/'src/cache_kernel.c')==provenance['kernel_source_sha256']
assert digest(root/'src/page_chase.c')==provenance['page_source_sha256']
assert digest(root/'src/cache_latency.c')==provenance['cache_latency_source_sha256']
manifest=json.loads((root/'data/raw/traces/kernel_study.parts.json').read_text())
d=hashlib.sha256();total=0
for part in manifest['parts']:
    b=(root/part['path']).read_bytes()
    assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256']
    total+=len(b);d.update(b)
assert total==manifest['bytes'] and d.hexdigest()==manifest['sha256']

audit=json.loads((root/'data/processed/validation.json').read_text())
assert (audit['main_mlc_measurements'],audit['kernel_trials'],audit['page_locality_trials'])==(360,20,50)
assert audit['cache_latency_trials']==35
assert audit['page_locality_followup_trials']==50 and audit['tlb_counter_status']=='TLB_ZERO_RESPONSE'
tlb=json.loads((root/'data/processed/tlb_attempt_audit.json').read_text())
assert tlb['tlb_counter_usable'] is False and tlb['trials']==50
assert digest(root/'data/raw/counter-attempts/tlb-study.zip')==tlb['archive_sha256']
assert digest(root/'scripts/pmu_tlb_study.wprp')==provenance['tlb_study_profile_sha256']
assert len(list((root/'plots').glob('*.png')))==10
assert len(list((root/'plots').glob('*.svg')))==10
for p in (root/'plots').glob('*.png'):
    with Image.open(p) as image:
        assert image.width>=800 and image.height>=400,p
        image.verify()
for p in root.rglob('*.md'):
    if 'build' in p.relative_to(root).parts:continue
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if re.match(r'^[a-z]+:',link) or link.startswith('#'):continue
        path=link.split('#')[0]
        assert (p.parent/path).exists(),(p,link)

files=[p for p in root.rglob('*') if p.is_file() and not any(x in {'build','bin','runs','.venv','__pycache__'} for x in p.relative_to(root).parts)]
assert max(p.stat().st_size for p in files)<25*1024*1024
result=dict(status='PASS',main_mlc_observations=360,kernel_trials=20,page_trials=50,
            cache_latency_trials=35,page_locality_followup_trials=50,tlb_counter_status='EXCLUDED_ZERO_RESPONSE',raw_files_checked=len(raw),figure_pairs=10,submission_files=len(files),
            largest_file_bytes=max(p.stat().st_size for p in files),
            notes='Raw archive checksums/CRC, source hashes, trace parts, observation counts, image readability and local Markdown links checked. analyze.py performs detailed numerical/coverage checks. decode_counters.py performs the ETL checks.')
(root/'data/processed/integrity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
