"""Restore the main compressed trace from browser-uploadable parts."""
from pathlib import Path
import hashlib, json, os

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'data/raw/traces/kernel_study.parts.json').read_text())
destination=root/'build/traces'/manifest['archive_name']
destination.parent.mkdir(parents=True,exist_ok=True)
temporary=destination.with_suffix('.tmp')
digest=hashlib.sha256();total=0
try:
    with temporary.open('wb') as output:
        for item in manifest['parts']:
            data=(root/item['path']).read_bytes()
            assert len(data)==item['bytes'], item['path']
            assert hashlib.sha256(data).hexdigest()==item['sha256'], item['path']
            output.write(data);digest.update(data);total+=len(data)
    assert total==manifest['bytes'] and digest.hexdigest()==manifest['sha256']
    os.replace(temporary,destination)
finally:
    temporary.unlink(missing_ok=True)
print(destination)
