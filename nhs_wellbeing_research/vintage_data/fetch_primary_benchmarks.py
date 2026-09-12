#!/usr/bin/env python3
"""Restore archived official benchmark payloads, checking both stored digests."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import urllib.request

HERE = Path(__file__).resolve().parent
CAPTURES = {2023: '20240705035334', 2024: '20250427122552'}


def main():
    sources = json.loads((HERE/'archived_benchmark_manifest.json').read_text())
    for vintage, capture in CAPTURES.items():
        source = next(r for r in sources if r['vintage'] == vintage and r['archive_capture'] == capture)
        path = HERE/source['local_file']
        if path.exists():
            data = path.read_bytes()
        else:
            request = urllib.request.Request(source['url'], headers={
                'User-Agent': 'Mozilla/5.0 (public academic data retrieval)'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if data[:2] == b'\x1f\x8b':
                data = gzip.decompress(data)
        assert hashlib.sha256(data).hexdigest() == source['sha256']
        assert base64.b32encode(hashlib.sha1(data).digest()).decode() == source['cdx_digest_sha1_base32']
        if not path.exists():
            path.write_bytes(data)
        print(vintage, path.name, len(data), 'SHA-256 and archive CDX SHA-1 verified')


if __name__ == '__main__':
    main()
