#!/usr/bin/env python3
"""Create employed-adult finite-file replay frames from CDC public ASCII data.

No statistical sampling, tuning or policy experiment is performed here.
"""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import json
import math
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/raw'
OUT = ROOT/'data/processed'
FIELDS = ('_STATE', '_PSU', 'MENTHLTH', 'EMPLOY1', '_STSTR', '_LLCPWT', '_MENT14D')
EXPECTED_ROWS = {2023: 433323, 2024: 457670}
# Published full-file codebook frequencies provide an independent basic check.
EXPECTED_MENTAL = {
    2023: {'1-30':168189, '88':257026, '77':5992, '99':2113, 'blank':3},
    2024: {'1-30':179605, '88':269909, '77':5594, '99':2559, 'blank':3}}
EXPECTED_EMPLOYED = {2023: {'1':177871, '2':37923}, 2024: {'1':186378, '2':39146}}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def text_from_zip(filename):
    with zipfile.ZipFile(RAW/filename) as archive:
        member = archive.namelist()[0]
        return archive.read(member).decode('latin1'), member


def layout(year):
    text, member = text_from_zip(f'SASOUT{year%100}_LLCP.zip')
    result = {}
    for name in FIELDS:
        found = re.search(r'^'+re.escape(name)+r'\s+(\d+)(?:-(\d+))?\s', text, re.M)
        assert found, (year, name)
        start = int(found.group(1)); end = int(found.group(2) or start)
        result[name] = (start-1, end)
    return result, member


def state_names(year):
    text, member = text_from_zip(f'codebook{year%100}_llcp-v2-508.zip')
    text = html.unescape(text).replace('\xa0', ' ')
    begin = text.index('SAS Variable Name: _STATE')
    end = text.index('SAS Variable Name:', begin+25)
    names = {}
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', text[begin:end], re.S|re.I):
        cells = [' '.join(re.sub('<[^>]+>', ' ', cell).split())
                 for cell in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', row, re.S|re.I)]
        if len(cells) >= 2 and re.fullmatch(r'\d{1,2}', cells[0]):
            names[f'{int(cells[0]):02d}'] = cells[1]
    assert len(names) == (52 if year == 2023 else 53), (year, names)
    return names, member


def write_csv(path, rows):
    rows = list(rows)
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def parse_year(year, sources):
    positions, sas_member = layout(year)
    names, codebook_member = state_names(year)
    filename = f'LLCP{year}ASC.zip'
    source_sha = sources[filename]['sha256']
    assert sha(RAW/filename) == source_sha
    total = 0
    mental_marginal = Counter(); employment_marginal = Counter(); lengths = Counter()
    by_state = defaultdict(Counter)
    complete = []
    published_category_matches = 0
    published_category_inconsistencies = []
    with zipfile.ZipFile(RAW/filename) as archive:
        assert len(archive.namelist()) == 1
        member = archive.namelist()[0]
        with archive.open(member) as stream:
            for number, record in enumerate(stream, 1):
                record = record.rstrip(b'\r\n')
                lengths[len(record)] += 1
                raw = {name: record[a:b].decode('ascii').strip() for name, (a,b) in positions.items()}
                total += 1
                state = f'{int(raw["_STATE"]):02d}'
                assert state in names
                employment = raw['EMPLOY1'] or 'blank'
                mental = raw['MENTHLTH'] or 'blank'
                if mental.isdigit() and 1 <= int(mental) <= 30:
                    category = '1-30'; days = int(mental)
                elif mental == '88':
                    category = mental; days = 0
                else:
                    assert mental in {'77', '99', 'blank'}, (year, number, mental)
                    category = mental; days = None
                mental_marginal[category] += 1
                employment_marginal[employment] += 1
                by_state[state]['all_records'] += 1
                if employment not in {'1', '2'}:
                    by_state[state]['not_employed_or_employment_missing'] += 1
                    continue
                by_state[state]['employed_all'] += 1
                if days is None:
                    by_state[state]['employed_mental_'+category] += 1
                    continue
                weight = float(raw['_LLCPWT']) if raw['_LLCPWT'] else None
                assert weight is not None and math.isfinite(weight) and weight > 0
                assert raw['_STSTR'].isdigit() and raw['_PSU'].isdigit()
                derived_category = 1 if days == 0 else 2 if days < 14 else 3
                if int(raw['_MENT14D']) == derived_category:
                    published_category_matches += 1
                else:
                    published_category_inconsistencies.append(dict(source_record_ordinal=number,
                        state=state, mental_unhealthy_days=days, source_mental_category=int(raw['_MENT14D']),
                        category_from_core_answer=derived_category,
                        disposition='Core MENTHLTH answer retained; no inferred correction or outcome-based exclusion'))
                by_state[state]['employed_complete'] += 1
                # Stable local ID made only from the source checksum and physical
                # row ordinal; it is not a person identifier or a longitudinal ID.
                identifier = hashlib.sha256(f'{year}:{source_sha}:{number}'.encode()).hexdigest()[:24]
                complete.append(dict(year=year, state=state, state_name=names[state],
                    health=(30-days)/3, weight=weight, stratum=raw['_STSTR'], psu=raw['_PSU'],
                    anonymrow=identifier, mental_unhealthy_days=days,
                    frequent_mental_distress=int(days >= 14), employment_code=int(employment),
                    employment_category='employed_for_wages' if employment == '1' else 'self_employed',
                    is_state_or_dc=int(int(state) <= 56)))
    assert total == EXPECTED_ROWS[year]
    assert dict(mental_marginal) == EXPECTED_MENTAL[year]
    for key, expected in EXPECTED_EMPLOYED[year].items():
        assert employment_marginal[key] == expected
    audit = dict(year=year, source_file=filename, source_sha256=source_sha, source_member=member,
                 sas_member=sas_member, codebook_member=codebook_member,
                 parsed_fields_one_based={name: [a+1,b] for name,(a,b) in positions.items()},
                 total_records=total, observed_record_lengths=dict(lengths),
                 states_and_territories=len(names), state_names=names,
                 mental_codebook_marginals_match=True, employment_codebook_marginals_match=True,
                 mental_marginal=dict(mental_marginal), employment_marginal=dict(employment_marginal),
                 employed_total=sum(EXPECTED_EMPLOYED[year].values()),
                 employed_valid_mental_records=len(complete),
                 published_mental_category_checks=published_category_matches,
                 published_mental_category_inconsistencies=published_category_inconsistencies,
                 group_counts={state: dict(counts) for state,counts in sorted(by_state.items())})
    return complete, audit


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = json.loads((ROOT/'data/brfss_source_manifest.json').read_text())['sources']
    years, audits = {}, {}
    for year in (2023, 2024):
        years[year], audits[year] = parse_year(year, sources)
        write_csv(OUT/f'brfss_employed_{year}_all_areas.csv', years[year])
        print(year, 'full-file records', audits[year]['total_records'], 'valid employed', len(years[year]), flush=True)
    common = sorted(set(row['state'] for row in years[2023] if row['is_state_or_dc']) &
                    set(row['state'] for row in years[2024] if row['is_state_or_dc']))
    assert len(common) == 48 and not {'21','42','47'} & set(common)
    combined = []
    group_summaries = []
    for year in (2023, 2024):
        selected = [row for row in years[year] if row['state'] in common]
        write_csv(OUT/f'brfss_employed_{year}.csv', selected)
        combined.extend(selected)
        for state in common:
            rows = [row for row in selected if row['state'] == state]
            nn = len(rows); weights = [r['weight'] for r in rows]; health = [r['health'] for r in rows]
            total_weight = math.fsum(weights)
            mean = math.fsum(health)/nn
            variance = math.fsum((x-mean)**2 for x in health)/nn
            group_summaries.append(dict(year=year, state=state, state_name=rows[0]['state_name'],
                n_complete=nn, employed_all=audits[year]['group_counts'][state]['employed_all'],
                n_mental_missing=audits[year]['group_counts'][state]['employed_all']-nn,
                finite_file_unweighted_mean=mean,
                finite_file_variance=variance, finite_file_standard_deviation=math.sqrt(variance),
                finite_file_weighted_ratio=math.fsum(w*h for w,h in zip(weights,health))/total_weight,
                sum_survey_weight=total_weight, mean_survey_weight=total_weight/nn,
                kish_weight_concentration_n=total_weight**2/math.fsum(w*w for w in weights),
                minimum_survey_weight=min(weights), maximum_survey_weight=max(weights),
                observed_strata=len({r['stratum'] for r in rows}),
                observed_psus=len({r['psu'] for r in rows})))
    write_csv(OUT/'brfss_employed_2023_2024.csv', combined)
    write_csv(OUT/'brfss_group_reference.csv', group_summaries)
    assert len({r['anonymrow'] for r in combined}) == len(combined)
    result = dict(status='passed', created_at_utc=datetime.now(timezone.utc).isoformat(),
        parser_sha256=sha(Path(__file__)), source_manifest_sha256=sha(ROOT/'data/brfss_source_manifest.json'),
        years=audits, common_states_and_dc=common, common_group_count=len(common),
        primary_rows_by_year={year:sum(r['year']==year for r in combined) for year in (2023,2024)},
        primary_group_size_ranges={year:[min(r['n_complete'] for r in group_summaries if r['year']==year),
                                        max(r['n_complete'] for r in group_summaries if r['year']==year)] for year in (2023,2024)},
        outputs={p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(OUT.glob('brfss_*.csv'))},
        interpretation='Finite public-file respondent frames, not latent mental health truth or state population prevalence',
        primary_target='Unweighted mean health among the complete employed respondents in each common state/DC and year',
        health_definition='health=(30-MENTHLTH_recoded_days)/3; 0 to 10, higher is better; not the NHS burnout composite',
        weights='Original _LLCPWT retained. Kish concentration n is not a design-adjusted effective sample size. Weighted subset ratios are not exactly unbiased under uniform sampling.',
        filtering='EMPLOY1 in {1,2}; MENTHLTH in {1,...,30,88}, with 88 recoded to zero; 77/99/blank excluded; common states/DC only for primary files')
    (OUT/'brfss_parse_manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('status','common_group_count','primary_rows_by_year','primary_group_size_ranges')},indent=2))


if __name__ == '__main__':
    main()
