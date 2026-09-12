#!/usr/bin/env python3
"""Retrieve official public BRFSS assets; preserve bytes and acquisition evidence."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'LLCP2023ASC.zip': 'https://www.cdc.gov/brfss/annual_data/2023/files/LLCP2023ASC.zip',
    'SASOUT23_LLCP.zip': 'https://www.cdc.gov/brfss/annual_data/2023/files/SASOUT23_LLCP.zip',
    'codebook23_llcp-v2-508.zip': 'https://www.cdc.gov/brfss/annual_data/2023/zip/codebook23_llcp-v2-508.zip',
    'variable_layout_2023.html': 'https://www.cdc.gov/brfss/annual_data/2023/llcp_varlayout_23_onecolumn.html',
    'annual_2023.html': 'https://www.cdc.gov/brfss/annual_data/annual_2023.html',
    'Overview_2023-508.pdf': 'https://www.cdc.gov/brfss/annual_data/2023/pdf/Overview_2023-508.pdf',
    'Complex_Sampling_2023.pdf': 'https://www.cdc.gov/brfss/annual_data/2023/pdf/Complex-Sampling-Weights-and-Preparing-Module-Data-for-Analysis-2023-508.pdf',
    'LLCP2024ASC.zip': 'https://www.cdc.gov/brfss/annual_data/2024/files/LLCP2024ASC.zip',
    'LLCP2024XPT.zip': 'https://www.cdc.gov/brfss/annual_data/2024/files/LLCP2024XPT.zip',
    'SASOUT24_LLCP.zip': 'https://www.cdc.gov/brfss/annual_data/2024/files/SASOUT24_LLCP.zip',
    'codebook24_llcp-v2-508.zip': 'https://www.cdc.gov/brfss/annual_data/2024/zip/codebook24_llcp-v2-508.zip',
    'variable_layout_2024.html': 'https://www.cdc.gov/brfss/annual_data/2024/llcp_varlayout_24_onecolumn.html',
    'annual_2024.html': 'https://www.cdc.gov/brfss/annual_data/annual_2024.html',
    'Overview_2024-508.pdf': 'https://www.cdc.gov/brfss/annual_data/2024/pdf/Overview_2024-508.pdf',
    'Complex_Sampling_2024.pdf': 'https://www.cdc.gov/brfss/annual_data/2024/pdf/Complex-Sampling-Weights-and-Preparing-Module-Data-for-Analysis-2024-508.pdf',
    'brfss_faq.html': 'https://www.cdc.gov/brfss/about/brfss_faq.htm',
    'agency_materials.html': 'https://www.cdc.gov/other/agencymaterials.html',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    raw = ROOT/'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT/'data/brfss_source_manifest.json'
    previous = json.loads(manifest_path.read_text()).get('sources', {}) if manifest_path.exists() else {}

    def retrieve(item):
        filename, url = item
        path = raw/filename
        if path.exists() and filename in previous:
            assert digest(path) == previous[filename]['sha256'], ('Cached source changed', filename)
            print('verified cached', filename, flush=True)
            return filename, previous[filename]
        request = urllib.request.Request(url)
        temporary = path.with_suffix(path.suffix+'.part')
        started = datetime.now(timezone.utc).isoformat()
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open('wb') as stream:
            headers = {key: response.headers.get(key) for key in ('Content-Type', 'Content-Length', 'Last-Modified', 'ETag')}
            final_url = response.url
            while block := response.read(1024*1024):
                stream.write(block)
        os.replace(temporary, path)
        entry = dict(url=url, resolved_url=final_url, retrieved_at_utc=started,
                     completed_at_utc=datetime.now(timezone.utc).isoformat(),
                     bytes=path.stat().st_size, sha256=digest(path), response_headers=headers,
                     origin='Official CDC public download; no account, key or login')
        if filename.endswith('.zip'):
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                entry['zip_members'] = [dict(name=v.filename, bytes=v.file_size, crc32=f'{v.CRC:08x}') for v in archive.infolist()]
        print('retrieved', filename, entry['bytes'], flush=True)
        return filename, entry

    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = dict(pool.map(retrieve, SOURCES.items()))
    result = dict(sources=entries, survey_years=[2023, 2024],
                  licence_evidence='BRFSS FAQ question 14 and CDC agency-materials terms are retained alongside source URLs; attribution and no endorsement required.',
                  retrieval_script_sha256=digest(Path(__file__)),
                  note='Local SHA-256 and ZIP CRC verify recorded byte identity/integrity; no publisher-provided SHA-256 is claimed.')
    manifest_path.write_text(json.dumps(result, indent=2)+'\n')
    print('manifest', manifest_path, flush=True)


if __name__ == '__main__':
    main()
