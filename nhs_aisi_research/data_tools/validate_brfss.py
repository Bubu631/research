#!/usr/bin/env python3
"""Independent fixed-offset row checks and 2024 ASCII/XPT agreement audit."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/raw'
OUT = ROOT/'data/processed'
# Independent fixed offsets verified against BOTH annual official SAS programs
# and required-field entries in the official variable-layout pages.
OFFSETS = {'_STATE':(0,2), '_PSU':(35,45), 'MENTHLTH':(103,105), 'EMPLOY1':(200,201),
           '_STSTR':(1409,1415), '_LLCPWT':(1748,1758), '_MENT14D':(1898,1899)}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    manifest = json.loads((OUT/'brfss_parse_manifest.json').read_text())
    source = json.loads((ROOT/'data/brfss_source_manifest.json').read_text())['sources']
    common = set(manifest['common_states_and_dc'])
    protected = {p.name:sha(p) for p in OUT.glob('brfss_*.csv')}
    direct_rows = {}
    ascii_2024 = []
    for year in (2023,2024):
        checked = 0
        with (OUT/f'brfss_employed_{year}.csv').open(newline='') as clean_stream:
            clean = iter(csv.DictReader(clean_stream))
            with zipfile.ZipFile(RAW/f'LLCP{year}ASC.zip') as archive:
                with archive.open(archive.namelist()[0]) as stream:
                    for ordinal, line in enumerate(stream,1):
                        fields = {key:line[a:b].decode('ascii').strip() for key,(a,b) in OFFSETS.items()}
                        if year == 2024:
                            ascii_2024.append([float(fields[key]) if fields[key] else np.nan for key in OFFSETS])
                        state = f'{int(fields["_STATE"]):02d}'
                        if state not in common or fields['EMPLOY1'] not in {'1','2'}:
                            continue
                        raw_mental = fields['MENTHLTH']
                        days = 0 if raw_mental == '88' else int(raw_mental) if raw_mental.isdigit() and 1<=int(raw_mental)<=30 else None
                        if days is None:
                            continue
                        row = next(clean)
                        assert int(row['year']) == year and row['state'] == state
                        assert int(row['mental_unhealthy_days']) == days
                        assert float(row['health']) == 10-days/3 or math.isclose(float(row['health']),10-days/3,abs_tol=2e-15)
                        assert 0 <= float(row['health']) <= 10
                        assert float(row['weight']) == float(fields['_LLCPWT']) > 0
                        assert row['stratum'] == fields['_STSTR'] and row['psu'] == fields['_PSU']
                        assert int(row['employment_code']) == int(fields['EMPLOY1'])
                        assert int(row['frequent_mental_distress']) == int(days>=14)
                        expected_id = hashlib.sha256(f'{year}:{source[f"LLCP{year}ASC.zip"]["sha256"]}:{ordinal}'.encode()).hexdigest()[:24]
                        assert row['anonymrow'] == expected_id
                        checked += 1
            assert next(clean,None) is None
        assert checked == manifest['primary_rows_by_year'][str(year)]
        direct_rows[year] = checked
        print('Direct fixed-offset clean-row checks passed',year,checked,flush=True)
    expected = np.asarray(ascii_2024)
    del ascii_2024
    keys = list(OFFSETS)
    weight_j = keys.index('_LLCPWT')
    exact_j = [j for j in range(len(keys)) if j != weight_j]
    pointer = 0
    weight_max_error = 0.
    mismatch_records = []
    with zipfile.ZipFile(RAW/'LLCP2024XPT.zip') as archive:
        with archive.open(archive.namelist()[0]) as stream:
            chunks = pd.read_sas(stream,format='xport',chunksize=25000,iterator=True)
            for frame in chunks:
                actual = frame[keys].to_numpy(dtype=float)
                reference = expected[pointer:pointer+len(actual)]
                assert np.array_equal(actual[:,exact_j],reference[:,exact_j],equal_nan=True), ('ASCII/XPT categorical or design field mismatch',pointer)
                weight_error = float(np.max(abs(actual[:,weight_j]-reference[:,weight_j])))
                weight_max_error = max(weight_max_error,weight_error)
                assert np.allclose(actual[:,weight_j],reference[:,weight_j],atol=5e-5,rtol=5e-9,equal_nan=True)
                # Recheck the four inconsistent derived categories independently
                # in SAS transport data, with original core answers unchanged.
                for issue in manifest['years']['2024']['published_mental_category_inconsistencies']:
                    index = issue['source_record_ordinal']-1
                    if pointer <= index < pointer+len(actual):
                        row = actual[index-pointer]
                        days_raw = row[keys.index('MENTHLTH')]
                        mismatch_records.append(dict(source_record_ordinal=index+1,
                            ascii_and_xpt_core_answer_equal=True,
                            xpt_mental_core_code=int(days_raw),xpt_published_category=int(row[keys.index('_MENT14D')]),
                            state=f'{int(row[keys.index("_STATE")]):02d}'))
                pointer += len(actual)
    assert pointer == 457670 and len(mismatch_records) == 4
    assert protected == {p.name:sha(p) for p in OUT.glob('brfss_*.csv')}
    result = dict(status='passed',checked_at_utc=datetime.now(timezone.utc).isoformat(),
                  validator_sha256=sha(Path(__file__)), primary_rows_checked_against_fixed_ASCII_offsets=direct_rows,
                  complete_ascii_xpt_crosscheck_rows=pointer, compared_fields=keys,
                  categorical_and_design_fields_exactly_equal=True,
                  maximum_ASCII_weight_rounding_absolute_error=weight_max_error,
                  documented_derived_category_inconsistencies_confirmed_in_XPT=mismatch_records,
                  derived_CSVs_unchanged=True, derived_CSV_sha256=protected,
                  source_sha256={f'source_{name}':entry['sha256'] for name,entry in source.items() if name.endswith('ASC.zip') or name.endswith('XPT.zip')},
                  numpy_version=np.__version__,pandas_version=pd.__version__,
                  scope='File parsing and record consistency; not validation of survey responses, population representativeness, latent mental health, or adaptive-policy validity')
    (OUT/'brfss_independent_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
