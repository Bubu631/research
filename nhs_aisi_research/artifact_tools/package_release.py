"""Package local research artifacts; does not upload, publish, or submit."""
from pathlib import Path
import hashlib,json,shutil,zipfile
from datetime import datetime,timezone
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'output/release'
DEST.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_zip(target,entries):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for source,name in entries:z.write(source,name)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None

def main():
    copies={'paper/full.pdf':'nhs_aisi_full_paper.pdf','paper/anonymous.pdf':'nhs_aisi_anonymous.pdf',
            'paper/supplement.pdf':'nhs_aisi_supplement.pdf','results/nhs_aisi_results.xlsx':'nhs_aisi_results.xlsx',
            'docs/nhs_decision_brief.pdf':'nhs_aisi_decision_brief.pdf','docs/upgrade_summary_zh.md':'nhs_aisi_upgrade_summary_zh.md'}
    for src,name in copies.items():shutil.copy2(ROOT/src,DEST/name)
    common=['main_content.tex','extended_content.tex','supplement_content.tex','theory_sections.tex','theory_proofs.tex','references.bib']
    shared=[(ROOT/'paper'/p,p) for p in common]
    shared +=[(p,str(p.relative_to(ROOT/'paper'))) for folder in ['figures','tables'] for p in sorted((ROOT/'paper'/folder).glob('*')) if p.suffix in {'.pdf','.tex'} and p.name!='full_grid.tex']
    write_zip(DEST/'nhs_aisi_arxiv_source.zip',[(ROOT/'paper/full.tex','main.tex'),(ROOT/'paper/full.bbl','main.bbl')]+shared)
    anonymous=[(ROOT/'paper'/p,p) for p in ['anonymous.tex','anonymous.bbl','supplement.tex','supplement.bbl','aaai2027.sty','aaai2027.bst','author_kit_manifest.json']]
    write_zip(DEST/'nhs_aisi_anonymous_source.zip',anonymous+shared)
    exclude_parts={'raw','__pycache__','node_modules','.venv','.git','qa'}
    exclude_ext={'.pyc','.aux','.log','.blg','.fls','.fdb_latexmk','.out'}
    entries=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p.is_symlink():continue
        rel=p.relative_to(ROOT)
        if any(x in exclude_parts for x in rel.parts) or rel.parts[0]=='output':continue
        if p.suffix in exclude_ext or 'smoke' in p.name or p.name=='.DS_Store':continue
        if p.name=='full_grid.tex':continue
        entries.append((p,str(Path('nhs_aisi_research')/rel)))
    write_zip(DEST/'nhs_aisi_reproducibility.zip',entries)
    outputs={}
    for name in list(copies.values())+['nhs_aisi_arxiv_source.zip','nhs_aisi_anonymous_source.zip','nhs_aisi_reproducibility.zip']:
        p=DEST/name;data={'bytes':p.stat().st_size,'sha256':sha(p)}
        if p.suffix=='.pdf':data['pages']=len(PdfReader(p).pages)
        outputs[name]=data
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'outputs':outputs,
      'original_nhs_pdf_sha256':sha(DEST/'nhs_wellbeing_paper.pdf'),
      'original_nhs_expected_sha256':'051d8aefbc73aed35227fa2e9ab662cb07cb028dd0b2c917b232b1698156040d',
      'scope':'AISI-oriented upgrade, not submitted or published; previous release preserved.'}
    assert manifest['original_nhs_pdf_sha256']==manifest['original_nhs_expected_sha256']
    (DEST/'nhs_aisi_release_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(outputs,indent=2))
if __name__=='__main__':main()
