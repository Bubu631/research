#!/usr/bin/env python3
"""Parse the official 2025-release NHS benchmark workbook into a tidy panel.

This is a retrospectively harmonized 2025 reporting-frame panel, not a sequence
of original data vintages. No scores, weights, eligible populations or precision
estimates are imputed. Nominal base counts are retained as published.
"""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import openpyxl

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
OUT=ROOT/'data/processed'
YEARS=range(2021,2026)
TRUST_SHEETS={'Acute&Acute Community Trusts','Acute Specialist Trusts',
              'MH&LD, MH, LD&Community Trusts','Community Trusts','Ambulance Trusts'}
# Official 2025 Technical Guide section 8.1, printed pages 32–33.
NO_HISTORY={
 'G6V2S':'Acquisition of RRP by TAF; new North London trust',
 'NDJ':'Substantial workforce-size change',
 'NQV':'No participation in 2024; guide names Medway but workbook names Bromley (source discrepancy)',
 'NTV':'Substantial workforce-size change',
 'QE1':'No participation in 2024',
 'QHM':'Substantial workforce-size change',
 'QNC':'Substantial workforce-size change',
 'RAL':'Acquisition of RAP by RAL',
 'RAX':'Acquisition of RY9 by RAX',
 'RQ3':'CAMHS transfer from RQ3 to RXT',
 'RTX':'Substantial workforce-size change',
 'RW1':'Acquisition of R1C by RW1',
 'RXL':'OneLSC workforce transfer from RXL to RXR',
 'RXR':'OneLSC workforce transfer from RXL to RXR',
 'RXT':'CAMHS transfer from RQ3 to RXT',
}
# Earlier official guides explain partial histories retained in the 2025 frame.
# These are metadata explanations, not additional score-based exclusions.
EARLIER_HISTORY={
 'RH8':(2022,'Merger of RH8 and RBZ; no comparable pre-2022 history'),
 'RM3':(2022,'Merger of RM3 and RW6; no comparable pre-2022 history'),
 'RA9':(2023,'Historical sample-drawing errors; no comparable pre-2023 history'),
 'RWK':(2023,'Historical sample-drawing errors; 2023 guide supersedes earlier 2022 cutoff'),
 'RBN':(2023,'Merger of RBN and RVY; no comparable pre-2023 history'),
 'RH5':(2023,'Merger of RA4 and RH5; no comparable pre-2023 history'),
 'RX2':(2024,'CAMHS transfer from RX2 to RW1; no comparable pre-2024 history'),
}
METRICS={
 'burnout_score':('PP4_2',1,'0–10; higher = less burnout'),
 'burnout_n':('PP4_2_n',1,'nominal count with a valid composite score'),
 'n_resp':('response_rate_n',1,'total completed questionnaires'),
 'response_rate':('response_rate',1,'0–1; published organisation-specific rate'),
 'wellbeing_action':('q11a',1,'0–1 agreeing or strongly agreeing'),
 'wellbeing_action_n':('q11a_n',1,'nominal valid question responses'),
 'intent_leave':('q26a',1,'0–1 agreeing or strongly agreeing that they often think about leaving'),
 'intent_leave_n':('q26a_n',1,'nominal valid question responses'),
 'thinking_about_leaving_score':('M_1',1,'0–10; higher = less intention to leave'),
 'thinking_about_leaving_n':('M_1_n',1,'nominal valid composite responses'),
 'work_related_stress':('q11c',1,'0–1 yes to feeling unwell due to work-related stress'),
 'work_related_stress_n':('q11c_n',1,'nominal valid question responses'),
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def number(value):
    if value is None or (isinstance(value,str) and value.strip() in {'','*','-','NA','N/A','n/a'}):return None
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):
        raise ValueError(f'Unexpected cell value: {value!r}')
    return value

def write_csv(path, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    path=RAW/'benchmark_2021_2025_v2.xlsx'
    source=json.loads((ROOT/'data/source_manifest.json').read_text())['sources'][path.name]
    assert sha(path)==source['sha256']
    workbook=openpyxl.load_workbook(path,read_only=True,data_only=True)
    rows=[];orgs=[];seen=set();missing=[];groups={}
    for sheet in list(workbook)[2:]:
        iterator=sheet.iter_rows(values_only=True); headers=next(iterator)
        if headers[:2]!=('org_id','org_name'):raise ValueError(sheet.title)
        indices={h:i+1 for i,h in enumerate(headers)}
        for excel_row,values in enumerate(iterator,2):
            original=dict(zip(headers,values));code=original['org_id']
            if code is None:continue
            if code in seen:raise ValueError(f'Duplicate reporting unit {code}')
            seen.add(code)
            present=[y for y in YEARS if number(original.get(f'PP4_2_{y}')) is not None]
            complete=int(len(present)==5 and code not in NO_HISTORY)
            is_trust=int(sheet.title in TRUST_SHEETS)
            counts=groups.setdefault(sheet.title,dict(reporting_units=0,complete_five_year=0))
            counts['reporting_units']+=1;counts['complete_five_year']+=complete
            orgs.append(dict(org_code=code,org_name=original['org_name'],benchmark_group=sheet.title,
                is_trust=is_trust,available_years=';'.join(map(str,present)),
                complete_five_year_history=complete,official_2025_no_history=int(code in NO_HISTORY),
                comparability_reason=NO_HISTORY.get(code,EARLIER_HISTORY[code][1] if code in EARLIER_HISTORY else 'All five official histories available' if complete else
                    'Earlier histories not provided in 2025 workbook; no values backfilled')))
            for year in YEARS:
                item=dict(org_code=code,org_name=original['org_name'],year=year,
                    benchmark_group=sheet.title,benchmark_group_vintage=2025,
                    is_trust=is_trust,reporting_unit_type='trust_sector' if code in {'R1F1','R1F2'} else 'trust' if is_trust else 'other_organisation',
                    legal_org_code='R1F' if code in {'R1F1','R1F2'} else code,
                    result_available=int(year in present),
                    historically_comparable=int(year in present and code not in NO_HISTORY),
                    complete_five_year_history=complete,official_2025_no_history=int(code in NO_HISTORY),
                    comparability_reason=orgs[-1]['comparability_reason'])
                cells={}
                for name,(stem,factor,_) in METRICS.items():
                    header=f'{stem}_{year}'
                    if header not in indices:raise ValueError((sheet.title,header))
                    value=number(original[header]);item[name]=None if value is None else value*factor
                    if value is not None and (name.endswith('_n') or name=='n_resp'):
                        if abs(value-round(value))>1e-9:raise ValueError((code,header,value))
                        item[name]=int(round(value))
                    cells[name]=f'{openpyxl.utils.get_column_letter(indices[header])}{excel_row}'
                    if value is None:missing.append(dict(org_code=code,year=year,field=name,source_cell=cells[name],
                        source_sheet=sheet.title,reason='Blank or suppressed in source; not imputed'))
                item.update(n_eligible=None,n_eligible_source='Not directly published in this workbook',
                    n_eligible_from_org_rate=None,n_eligible_derivation='Not computed where source response count or organisation rate is absent',
                    n_eff=None,burnout_se=None,burnout_individual_sd=None,
                    precision_metadata='Individual weights and composite SD/SE unavailable; burnout_n is nominal',
                    release_vintage=2025,weighting=('Unweighted' if sheet.title in {'ICBs','Community Surgical Services'}
                        else 'Occupational group; histories reweighted to 2025 group proportions'),
                    source_file=path.relative_to(ROOT).as_posix(),source_sheet=sheet.title,source_row=excel_row,
                    source_sha256=source['sha256'],source_cells=json.dumps(cells,sort_keys=True,separators=(',',':')))
                if item['n_resp'] is not None and item['response_rate']:
                    # This is an explicitly labelled algebraic denominator, NOT a
                    # directly observed eligible count or a national-rate imputation.
                    item['n_eligible_from_org_rate']=item['n_resp']/item['response_rate']
                    item['n_eligible_derivation']='Published total responses / published organisation-specific rate; approximate in 2021 due to rate precision'
                if item['burnout_score'] is not None:
                    assert 0<=item['burnout_score']<=10
                    assert item['burnout_n']>=10
                    assert item['n_resp']>=item['burnout_n']
                for field in ['response_rate','wellbeing_action','intent_leave','work_related_stress']:
                    if item[field] is not None:assert 0<=item[field]<=1,(code,year,field)
                rows.append(item)
    rows.sort(key=lambda r:(r['org_code'],r['year']));orgs.sort(key=lambda r:r['org_code'])
    assert len(rows)==len(seen)*5
    assert len({(r['org_code'],r['year']) for r in rows})==len(rows)
    assert all(not o['complete_five_year_history'] for o in orgs if o['org_code'] in NO_HISTORY)
    write_csv(OUT/'nhs_staff_survey_panel_2021_2025.csv',rows)
    write_csv(OUT/'organisation_cohort.csv',orgs)
    write_csv(OUT/'missingness_cells.csv',missing)
    sources=json.loads((ROOT/'data/source_manifest.json').read_text())['sources']
    events=[]
    for code in sorted(set(NO_HISTORY)|set(EARLIER_HISTORY)):
        guide_year,reason=(2025,NO_HISTORY[code]) if code in NO_HISTORY else EARLIER_HISTORY[code]
        guide=sources[f'technical_{guide_year}.pdf']
        events.append(dict(org_code=code,guide_year=guide_year,guide_section='8.1',
            reason=reason,source_url=guide['url'],source_sha256=guide['sha256']))
    write_csv(OUT/'historical_comparability_events.csv',events)
    dictionary={name:dict(source_variable=stem+'_YEAR',multiplication_factor=factor,units=units,
        missing='blank/suppressed source retained as empty CSV field') for name,(stem,factor,units) in METRICS.items()}
    dictionary.update(
        org_code=dict(definition='2025 NSS reporting-unit identifier; not necessarily one independent legal trust'),
        org_name=dict(definition='Organisation name used in the 2025 source, applied to its reported history'),
        year=dict(definition='Survey year, not publication year'),
        benchmark_group=dict(definition='2025 reporting benchmark group; historical observations retain this current classification'),
        historically_comparable=dict(definition='Result is provided for this year and organisation is absent from the 2025 no-historical-comparison list; does not establish stable staff membership'),
        complete_five_year_history=dict(definition='All five official burnout scores available and no 2025 no-history flag; intended complete-history cohort indicator'),
        n_eligible=dict(definition='Empty: eligible population is not directly reported in the workbook; not imputed'),
        n_eligible_from_org_rate=dict(definition='Algebraic total n_resp / organisation-specific response_rate; explicitly derived, not directly observed. 2021 rates have limited precision. No national response rate used'),
        n_eff=dict(definition='Empty: individual analysis weights and item-specific missingness by weight group are unavailable'),
        burnout_se=dict(definition='Empty: no aggregate composite standard error supplied'),
        burnout_individual_sd=dict(definition='Empty: individual composite standard deviation unavailable; cannot reconstruct from marginal item percentages without covariance'),
        wellbeing_action=dict(source_variable='q11a_YEAR',units='proportion agreeing that organisation takes positive action; perceived action, not measured intervention allocation'),
        intent_leave=dict(source_variable='q26a_YEAR',units='proportion often thinking about leaving; intention, not actual subsequent exit',
            original_question_number_by_year={'2021':'Q22a','2022':'Q24a','2023':'Q26a','2024':'Q26a','2025':'Q26a'},
            harmonization='2025 workbook presents corresponding earlier questions under current q26a_YEAR names'),
        source_cells=dict(definition='JSON field-to-Excel-cell locator; source_sheet and source SHA retained separately'))
    other_fields={
      'benchmark_group_vintage':'Year whose reporting classification is used: 2025',
      'is_trust':'1 for the five official trust reporting groups; 0 for ICBs, social enterprises, community surgical services',
      'reporting_unit_type':'trust, trust_sector (R1F1/R1F2), or other_organisation',
      'legal_org_code':'R1F for the two Isle of Wight sectors, otherwise published org_code; not a comprehensive legal-successor crosswalk',
      'result_available':'1 if a numeric burnout score was published for this unit/year, including current-only units',
      'official_2025_no_history':'1 when code appears in section 8.1 of the 2025 technical guide',
      'comparability_reason':'Official 2022–2025 historical-comparability explanation, or missing-history/complete-history status; no outcome-based exclusion',
      'n_eligible_source':'Clarifies that direct eligibility counts are absent from this source',
      'n_eligible_derivation':'Clarifies derivation and rate-precision limitation for n_eligible_from_org_rate',
      'precision_metadata':'Distinguishes nominal counts from unavailable effective sample size and standard errors',
      'release_vintage':'Reporting release vintage used for all observations: 2025 survey release, published 2026',
      'weighting':'Source weighting for the organisation group; demographic exceptions do not affect retained outcome measures',
      'source_file':'Repository-relative raw workbook path',
      'source_sheet':'Exact workbook sheet name',
      'source_row':'One-based Excel row',
      'source_sha256':'SHA-256 of the original downloaded workbook',
    }
    dictionary.update({k:dict(definition=v) for k,v in other_fields.items()})
    assert set(dictionary)==set(rows[0]),set(rows[0])-set(dictionary)
    (OUT/'data_dictionary.json').write_text(json.dumps(dictionary,indent=2)+'\n')
    notes=[]
    for i,row in enumerate(workbook['Notes'].values,1):
        if any(v is not None for v in row):notes.append(dict(excel_row=i,variable=row[0],description=row[1]))
    (OUT/'source_variable_dictionary.json').write_text(json.dumps(notes,indent=2)+'\n')
    qc=dict(parsed_at_utc=datetime.now(timezone.utc).isoformat(),source_sha256=source['sha256'],
        parser_sha256=sha(Path(__file__)),openpyxl_version=openpyxl.__version__,
        rows=len(rows),reporting_units=len(orgs),trust_reporting_units=sum(o['is_trust'] for o in orgs),
        complete_trust_reporting_units=sum(o['is_trust']*o['complete_five_year_history'] for o in orgs),
        group_coverage=groups,available_score_rows_by_year={y:sum(r['year']==y and r['result_available'] for r in rows) for y in YEARS},
        directly_observed_eligible_counts=0,individual_weight_records=0,composite_standard_errors=0,
        source_caveats=['2025 reporting-frame/survivor cohort; not all organisations operating in each historical year',
            'Histories reweighted and recleaned in 2025; not a strict real-time vintage evaluation',
            'Trust sectors R1F1/R1F2 share legal code R1F',
            'Technical guide has NQV name discrepancy; workbook name retained; nontrust unit is excluded from primary cohort'],
        validation='Unique keys, complete coverage, numeric bounds, valid-count <= total-response counts, source hash and no-history exclusions passed')
    generated_names=['nhs_staff_survey_panel_2021_2025.csv','organisation_cohort.csv','missingness_cells.csv',
        'historical_comparability_events.csv','data_dictionary.json','source_variable_dictionary.json']
    qc['outputs']={name:sha(OUT/name) for name in generated_names}
    (OUT/'panel_manifest.json').write_text(json.dumps(qc,indent=2)+'\n')
    print(json.dumps({k:qc[k] for k in ['rows','reporting_units','trust_reporting_units','complete_trust_reporting_units','group_coverage','validation']},indent=2))

if __name__=='__main__':main()
