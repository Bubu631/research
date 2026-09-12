#!/usr/bin/env python3
"""Fetch official public NHS Staff Survey assets with immutable local provenance.

Existing downloads are verified and reused. Use --refresh to explicitly replace
them from the same URLs. This script submits no information to NHS services.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
MANIFEST = ROOT / 'data' / 'source_manifest.json'
PAGES = {
    'local_results.html': 'https://www.nhsstaffsurveys.com/results/local-results/',
    'national_results.html': 'https://www.nhsstaffsurveys.com/results/national-results/',
    'survey_documents.html': 'https://www.nhsstaffsurveys.com/survey-documents/',
    'faqs.html': 'https://www.nhsstaffsurveys.com/faqs/',
    'results_archive.html': 'https://www.nhsstaffsurveys.com/results/results-archive/',
}
ASSETS = {
    'benchmark_2021_2025_v2.xlsx': 'https://www.nhsstaffsurveys.com/static/be505cf2e70c080aa35d34279f68e3f2/NSS-Benchmark-report-excel-data-for-2021-2025-v2.xlsx',
    'detailed_2025.zip': 'https://www.nhsstaffsurveys.com/static/98d750b25a18cce79ff98383f0d6d1d4/NSS25-Detailed-spreadsheets.zip',
    # Static-query ID is exposed by the official archive page's JavaScript.
    'archive_catalog.json': 'https://www.nhsstaffsurveys.com/page-data/sq/d/4265973848.json',
    'example_RCF_benchmark_2025.pdf': 'https://cms.nhsstaffsurveys.com/app/reports/2025/RCF-benchmark-2025.pdf',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.href=None; self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.href=dict(attrs).get('href'); self.parts=[]
    def handle_data(self, data):
        if self.href is not None: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag=='a' and self.href is not None:
            self.links.append((' '.join(' '.join(self.parts).split()), self.href)); self.href=None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    RAW.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else dict(
        owner='NHS England; Staff Survey Coordination Centre at Picker Institute Europe',
        scope='Public substantive-staff organisation-level data; not individual or department observations',
        license_status='Public access confirmed; asset-specific reuse terms require review, no license inferred from accessibility',
        sources={})
    def fetch(name,url):
        path=RAW/name
        if path.exists() and not args.refresh:
            data=path.read_bytes()
            assert manifest['sources'][name]['sha256']==sha(data),name
            return data
        started=datetime.now(timezone.utc).isoformat()
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (public academic data retrieval)'})
        with urllib.request.urlopen(request,timeout=180) as response:
            data=response.read(); headers=dict(response.headers); final_url=response.url
        path.write_bytes(data)
        manifest['sources'][name]=dict(url=url,final_url=final_url,accessed_at_utc=started,
            downloaded_at_utc=datetime.now(timezone.utc).isoformat(),bytes=len(data),sha256=sha(data),
            content_type=headers.get('Content-Type'),last_modified=headers.get('Last-Modified'),etag=headers.get('ETag'),
            local_path=path.relative_to(ROOT).as_posix())
        MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n')
        print(f'{name}: {len(data):,} bytes',flush=True)
        return data
    for name,url in PAGES.items(): fetch(name,url)
    for name,url in ASSETS.items(): fetch(name,url)
    html=(RAW/'survey_documents.html').read_text(); links=Links();links.feed(html)
    targets={'technical_2025.pdf':'NHS Staff Survey 2025 Technical Guide (Updated',
             'understanding_2025.pdf':'NHS Staff Survey 2025 A Guide to Understanding and Using Results',
             'data_issue_2023.pdf':'Additional information regarding NSS23 data collection issue'}
    for name,prefix in targets.items():
        matches=[url for label,url in links.links if label.startswith(prefix)]
        if len(matches)!=1:raise ValueError((name,matches))
        fetch(name,urllib.request.urljoin(PAGES['survey_documents.html'],matches[0]))
    catalog=json.loads((RAW/'archive_catalog.json').read_text())
    for node in catalog['data']['allWpYear']['nodes']:
        item=node['archiveTemplate']; year=int(item['year'])
        if not 2021 <= year <= 2025: continue
        for block in item['flexibleContent']:
            for record in block.get('downloads',[]):
                label=record['name'].lower()
                if 'bank' in label or label.startswith('nssb'): continue
                kind=('technical' if 'technical' in label else 'detailed' if 'detailed' in label
                      else 'questionnaire' if 'questionnaire' in label else None)
                if not kind: continue
                file=record['file']['localFile']
                name=f'{kind}_{year}.{file["extension"]}'
                fetch(name,urllib.request.urljoin(PAGES['results_archive.html'],file['publicURL']))
    # Accessibility is not a copyright licence. Preserve the uncertainty rather
    # than applying an older data.gov.uk OGL listing to different 2021–2025 files.
    manifest['license_status']='Publicly accessible; no asset-specific permissive licence verified for these current files'
    manifest['license_audit']={
        'checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'site_copyright_notice':'Copyright NHS Staff Survey',
        'questionnaire_terms_url':PAGES['faqs.html'],
        'questionnaire_terms_summary':'FAQ requires express NHS England permission to reuse the questionnaire or subsets for other purposes; this retrieval is not administration of a new survey',
        'historical_catalog_url':'https://www.data.gov.uk/dataset/7e6cfa08-536a-4066-b7bd-a673c3034a49/national_nhs_staff_survey',
        'historical_catalog_caveat':'The old catalogue OGL label has not been verified to cover these 2021–2025 assets',
        'redistribution_status':'No new permission sought; retain raw third-party assets locally and do not attach a blanket code licence to them',
    }
    for name,item in manifest['sources'].items():
        item['license_id']=None
        item['license_status']='No asset-specific permissive licence verified'
        item['license_evidence_url']=PAGES['faqs.html']
        if name.startswith('questionnaire_'):
            item['additional_terms']='Official FAQ requires express permission to reuse the questionnaire for other purposes'
    manifest['fetch_script_sha256']=sha(Path(__file__).read_bytes())
    MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Source provenance:',MANIFEST)

if __name__=='__main__': main()
