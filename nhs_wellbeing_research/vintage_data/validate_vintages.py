#!/usr/bin/env python3
"""Independent OOXML value checks and descriptive vintage revision diagnostics."""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def read(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def main():
    records = read(HERE/'benchmark_vintage_panel.csv')
    count = 0
    for filename in sorted({r['source_file'] for r in records}):
        rows = [r for r in records if r['source_file'] == filename]
        with zipfile.ZipFile(HERE/filename) as z:
            book = ET.fromstring(z.read('xl/workbook.xml'))
            relationships = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
            targets = {e.attrib['Id']: e.attrib['Target'] for e in relationships}
            paths = {e.attrib['name']: targets[e.attrib['{'+NS['r']+'}id']]
                     for e in book.find('m:sheets', NS)}
            for name in sorted({r['source_sheet'] for r in rows}):
                target = paths[name]
                path = target.lstrip('/') if target.startswith('/') else 'xl/'+target
                checks = {}
                for row in rows:
                    if row['source_sheet'] != name:
                        continue
                    for metric, cell in json.loads(row['source_cells']).items():
                        checks[cell] = (metric, row[metric])
                found = set()
                for event, element in ET.iterparse(io.BytesIO(z.read(path)), events=('end',)):
                    if element.tag != '{'+NS['m']+'}c':
                        continue
                    cell = element.attrib['r']
                    if cell in checks:
                        metric, expected = checks[cell]
                        value = element.find('m:v', NS)
                        # Missing historical cells are stored as blanks/string
                        # markers and are not converted to zero by the parser.
                        if expected != '':
                            assert value is not None and element.attrib.get('t') != 's'
                            assert float(value.text) == float(expected), (filename, name, cell)
                            count += 1
                        found.add(cell)
                    element.clear()
                assert all(cell in found for cell, (_, expected) in checks.items() if expected != '')
    annual = read(HERE/'annual_release_current_year_panel.csv')
    annual_lookup = {(int(r['year']), r['org_code']): r for r in annual}
    annual_checks = {}
    for vintage in [2023, 2024]:
        rows = [r for r in records if int(r['release_vintage']) == vintage and int(r['year']) == vintage]
        differences = []
        for row in rows:
            other = annual_lookup[vintage, row['org_code']]
            assert row['burnout_n'] == other['burnout_n']
            if row['burnout_score']:
                differences.append(abs(float(row['burnout_score'])-float(other['burnout_score'])))
        assert max(differences) < 1e-12
        annual_checks[str(vintage)] = dict(matched_organisations=len(rows), nominal_counts_equal=True,
                                           maximum_score_difference=max(differences))
    main_panel = read(ROOT/'data/processed/nhs_staff_survey_panel_2021_2025.csv')
    cohort = read(ROOT/'data/processed/organisation_cohort.csv')
    primary = {r['org_code'] for r in cohort if r['is_trust'] == '1' and r['complete_five_year_history'] == '1'}
    vintage_sets = {y: {r['org_code'] for r in records if int(r['release_vintage']) == y
                       and r['is_trust'] == '1' and r['complete_history_in_vintage'] == '1'} for y in [2023, 2024]}
    shared = primary & vintage_sets[2023] & vintage_sets[2024]
    group_changes = {code: sorted({r['benchmark_group'] for r in records+main_panel if r['org_code'] == code})
                     for code in shared}
    group_changes = {k: v for k, v in group_changes.items() if len(v) > 1}
    lookup = {(r['org_code'], int(r['year'])): r for r in main_panel}
    revisions = {}
    for vintage in [2023, 2024]:
        differences, count_changes = [], []
        for row in records:
            if int(row['release_vintage']) != vintage or row['org_code'] not in shared:
                continue
            other = lookup[row['org_code'], int(row['year'])]
            differences.append(float(other['burnout_score'])-float(row['burnout_score']))
            delta_n = float(other['burnout_n'])-float(row['burnout_n'])
            if delta_n:
                count_changes.append(dict(org_code=row['org_code'], survey_year=int(row['year']),
                    original_vintage_n=float(row['burnout_n']), latest_vintage_n=float(other['burnout_n']), difference=delta_n))
        revisions[str(vintage)] = dict(matched_cells=len(differences),
            mean_absolute_score_revision=sum(abs(x) for x in differences)/len(differences),
            max_absolute_score_revision=max(abs(x) for x in differences),
            score_revisions_over_1e_10=sum(abs(x) > 1e-10 for x in differences), count_changes=count_changes)
    result = dict(status='passed', checked_at_utc=datetime.now(timezone.utc).isoformat(),
        direct_OOXML_numeric_cell_checks=count, annual_workbook_crosschecks=annual_checks,
        primary_cohort_size=len(primary), shared_all_three_vintages_size=len(shared),
        shared_all_three_org_codes=sorted(shared), group_changes=group_changes,
        revisions_to_2025_vintage=revisions,
        validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        primary_csv_sha256=hashlib.sha256((HERE/'benchmark_vintage_panel.csv').read_bytes()).hexdigest())
    (HERE/'independent_validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'shared_all_three_org_codes'}, indent=2))


if __name__ == '__main__':
    main()
