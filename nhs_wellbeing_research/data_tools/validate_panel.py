#!/usr/bin/env python3
"""Independent cell-locator and provenance check of the exported panel."""
import csv
import hashlib
import json
import math
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import openpyxl

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    sources=json.loads((ROOT/'data/source_manifest.json').read_text())['sources']
    for entry in sources.values():
        assert sha(ROOT/entry['local_path'])==entry['sha256']
    panel=list(csv.DictReader((OUT/'nhs_staff_survey_panel_2021_2025.csv').open()))
    dictionary=json.loads((OUT/'data_dictionary.json').read_text())
    assert set(panel[0])==set(dictionary)
    wb=openpyxl.load_workbook(ROOT/'data/raw/benchmark_2021_2025_v2.xlsx',data_only=True)
    checks=0
    for row in panel:
        sheet=wb[row['source_sheet']]
        assert sheet.cell(int(row['source_row']),1).value==row['org_code']
        for field,cell in json.loads(row['source_cells']).items():
            original=sheet[cell].value
            value=row[field]
            if original is None:
                assert value==''
            else:
                # Most percentage cells have percent formats; some q26a cells
                # use General. A separate detailed workbook below verifies the
                # units independently for all three optional 2025 measures.
                if field in {'response_rate','wellbeing_action','intent_leave','work_related_stress'}:
                    assert '%' in sheet[cell].number_format or sheet[cell].number_format=='General'
                assert math.isclose(float(value),float(original),rel_tol=1e-12,abs_tol=1e-12)
            checks+=1
    by_code={r['org_code']:r for r in panel if r['year']=='2025'}
    detailed_checks=0
    with ZipFile(ROOT/'data/raw/detailed_2025.zip') as archive:
        member=next(n for n in archive.namelist() if 'organisational results' in n)
        detail=openpyxl.load_workbook(BytesIO(archive.read(member)),read_only=True,data_only=True)
        for sheet_name,fields in [
            ('HEALTH WELLBEING SAFETY Q10-11',[('Q11a','wellbeing_action',['% Agree','% Strongly agree']),('Q11c','work_related_stress',['% Yes'])]),
            ('YOUR ORGANISATION Q25-26',[('Q26a','intent_leave',['% Agree','% Strongly agree'])])]:
            records=list(detail[sheet_name].iter_rows(values_only=True))
            questions=[];current=''
            for h in records[0]:
                if h is not None:current=str(h)
                questions.append(current)
            for prefix,field,options in fields:
                indices=[j for j,q in enumerate(questions) if q.startswith(prefix+' -') and records[4][j] in options]
                assert len(indices)==len(options)
                for record in records[5:]:
                    if record[0] not in by_code:continue
                    values=[record[j] for j in indices]
                    if not all(isinstance(v,(float,int)) for v in values):continue
                    observed=float(by_code[record[0]][field])
                    assert math.isclose(observed,sum(values)/100,rel_tol=1e-10,abs_tol=1e-10),(record[0],field)
                    detailed_checks+=1
    cohort=[r for r in panel if r['is_trust']=='1' and r['complete_five_year_history']=='1']
    assert len(cohort)==950 and len({r['org_code'] for r in cohort})==190
    assert len({r['legal_org_code'] for r in cohort})==189
    assert len({(r['org_code'],r['year']) for r in panel})==1190
    for row in panel:
        assert row['n_eff']==row['burnout_se']==row['burnout_individual_sd']==row['n_eligible']==''
    # A separate published PDF reports 1,475 completed questionnaires for RCF.
    # This verifies total responses are not mistaken for valid burnout responses.
    rcf=next(r for r in panel if r['org_code']=='RCF' and r['year']=='2025')
    assert int(rcf['n_resp'])==1475
    assert int(rcf['burnout_n'])==1473
    result=dict(status='passed',raw_source_hashes_checked=len(sources),source_cells_checked=checks,
        independent_2025_detailed_percentage_checks=detailed_checks,
        rows=len(panel),complete_trust_reporting_units=190,known_legal_ids_in_complete_cohort=189,
        dictionary_column_coverage='complete',panel_sha256=sha(OUT/'nhs_staff_survey_panel_2021_2025.csv'),
        validator_sha256=sha(Path(__file__)))
    (OUT/'validation_report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
