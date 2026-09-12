#!/usr/bin/env python3
"""Make searchable local documentation extracts; retain PDFs as authority."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import openpyxl
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; OUT=ROOT/'data/extracted'

def main():
    OUT.mkdir(exist_ok=True)
    manifest={}
    def extract(data,name,source):
        reader=PdfReader(io.BytesIO(data))
        text='\n'.join(f'\n--- PDF PAGE {i} ---\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages,1))
        target=OUT/(name+'.txt');target.write_text(text)
        manifest[target.name]=dict(source=source,pdf_sha256=hashlib.sha256(data).hexdigest(),pages=len(reader.pages),
            text_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    for p in sorted(RAW.glob('*.pdf')):extract(p.read_bytes(),p.stem,p.relative_to(ROOT).as_posix())
    for p in sorted(RAW.glob('questionnaire*.zip')):
        with zipfile.ZipFile(p) as z:
            for member in z.namelist():
                if member.endswith('.pdf'):
                    suffix=Path(member).stem.lower().replace(' ','_')
                    extract(z.read(member),p.stem+'_'+suffix,p.relative_to(ROOT).as_posix()+'::'+member)
    workbook=openpyxl.load_workbook(RAW/'benchmark_2021_2025_v2.xlsx',read_only=True,data_only=True)
    (OUT/'benchmark_notes.txt').write_text('\n'.join(f'{i}: '+' | '.join(str(v) for v in r if v is not None)
        for i,r in enumerate(workbook['Notes'].values,1)))
    (OUT/'extraction_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Extracted',len(manifest),'public PDFs for local source review.')

if __name__=='__main__':main()
