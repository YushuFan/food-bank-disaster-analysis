"""Copy a publication-only repository and create a ZIP (no raw files or env)."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=['README.md','.gitignore','pyproject.toml','requirements.txt','RELEASE_CHECKLIST.md']
DIRS=['src','sql','tests','scripts','docs','data/public','reports/figures']
EXTRA=['data/README.md','reports/FINDINGS.md','reports/report.html','reports/results.json']


def package(destination):
    if destination.exists():
        raise FileExistsError('Choose a new release directory; existing releases are preserved.')
    selected=[ROOT/p for p in FILES+EXTRA]
    for folder in DIRS:
        selected.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.pyo'])
    selected=sorted(set(selected))
    destination.mkdir(parents=True)
    hashes={}
    for source in selected:
        relative=source.relative_to(ROOT)
        target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        hashes[str(relative)]=hashlib.sha256(target.read_bytes()).hexdigest()
    (destination/'MANIFEST.json').write_text(json.dumps(hashes,indent=2)+'\n')
    archive=destination.with_suffix('.zip')
    if archive.exists():
        raise FileExistsError(archive)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(destination.rglob('*')):
            if f.is_file():z.write(f,Path(destination.name)/f.relative_to(destination))
    print(f'{len(hashes)} files + manifest; archive: {archive}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,required=True)
    package(p.parse_args().destination.resolve())
