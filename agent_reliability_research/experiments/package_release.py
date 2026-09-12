"""Package verified manuscript and reproducibility artifacts without raw data."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT.parent/'output/release';RELEASE.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pdf=RELEASE/'agent_audit_paper.pdf';shutil.copy2(ROOT/'paper/main.pdf',pdf)
source=RELEASE/'agent_audit_arxiv_source.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted((ROOT/'paper').iterdir()):
        if p.suffix in {'.tex','.bib','.bbl'} and p.name!='stateful_qa.tex':z.write(p,p.name)
    for p in sorted((ROOT/'figures').glob('*.png')):z.write(p,'figures/'+p.name)
    z.writestr('00_README.txt','Compile main.tex with pdfLaTeX and BibTeX. This is the complete extended manuscript. Source package compilation does not assert arXiv acceptance or conference-format compliance.\n')
repo=RELEASE/'agent_audit_reproducibility.zip'
included=[]
with zipfile.ZipFile(repo,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT);parts=rel.parts
        if any(x in {'__pycache__','.venv','.git','tokenizer_cache','previous_runs','pilot_estimation_central'} for x in parts):continue
        if len(parts)>=3 and parts[:3]==('data','swe_gym','raw'):continue
        if any(x.endswith('.partial.npz') for x in parts):continue
        if p.suffix in {'.pyc','.aux','.log','.out','.fls','.fdb_latexmk','.synctex'}:continue
        if p.name in {'paper_text.txt','manifest_in_progress.json'}:continue
        if 'stateful_qa' in p.name:continue
        z.write(p,'agent_reliability_research/'+str(rel));included.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':sha(p)})
    z.writestr('PACKAGE_MANIFEST.json',json.dumps({'files':included,'excluded':['private direction notes','raw third-party trajectory text','model weights','input token artifact','intermediate caches','redundant exploratory pilot']},indent=2))
manifest={'paper_title':'The Audit Complexity of Group-Relative Policy Updates','pages':24,'figures':4,'tables':3,
 'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [pdf,source,repo]},
 'reproducibility_files':len(included),'no_cloud_training_or_submission_claim':True}
(RELEASE/'agent_audit_release_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
# Inspect our own archive and verify every path before extracting for compilation.
check=Path.home()/'.cache/shengwei-agent-audit/source_build';check.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(source) as z:
    assert z.testzip() is None
    for name in z.namelist():
        q=Path(name)
        if q.is_absolute() or '..' in q.parts:raise ValueError('Unsafe archive path')
    z.extractall(check)
