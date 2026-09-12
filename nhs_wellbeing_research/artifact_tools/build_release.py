#!/usr/bin/env python3
"""Build the third paper's standalone public archives after explicit finalisation.

No scientific experiment is rerun and the first two papers' packages/manifests
are never touched. Default invocation only explains the finalisation guard.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT/'paper'
DESTINATION = ROOT.parent/'output/release'
PACKAGE_NAMES = ('nhs_wellbeing_source.zip', 'nhs_wellbeing_research.zip')
PDF_NAME = 'nhs_wellbeing_paper.pdf'
MANIFEST_NAME = 'nhs_wellbeing_manifest.json'
VALIDATION_NAME = 'nhs_wellbeing_package_validation.json'
SOURCE_VALIDATION_NAME = 'nhs_wellbeing_source_validation.json'
CHECKSUM_NAME = 'nhs_wellbeing_SHA256SUMS.txt'
TEXT_EXTENSIONS = {'.py', '.mjs', '.js', '.md', '.txt', '.json', '.csv', '.tex', '.bib', '.bbl', '.cff', '.toml', '.yml', '.yaml'}
REQUIRED = (
    'README.md', 'Makefile', 'requirements.txt', 'paper/main.tex',
    'paper/main.bbl', 'paper/references.bib', 'paper/main.pdf',
    'data/source_manifest.json', 'data/processed/nhs_staff_survey_panel_2021_2025.csv',
    'data/processed/organisation_cohort.csv', 'data/processed/data_dictionary.json',
    'data_tools/fetch_sources.py', 'data_tools/parse_panel.py', 'data_tools/validate_panel.py',
    'vintage_data/fetch_primary_benchmarks.py', 'vintage_data/parse_vintages.py',
    'vintage_data/validate_vintages.py', 'vintage_data/archived_benchmark_manifest.json',
    'vintage_data/source_manifest.json', 'vintage_data/benchmark_vintage_panel.csv',
    'vintage_data/annual_release_current_year_panel.csv', 'experiments/empirical.py',
    'experiments/vintage_empirical.py', 'experiments/simulate.py', 'experiments/common.py',
    'experiments/report.py', 'experiments/verify_empirical.py',
    'results/empirical_independent_audit.json', 'docs/analysis_protocol.md',
    'docs/vintage_audit.md', 'docs/empirical_independent_audit.md',
    'docs/release_package_checks.md', 'artifact_tools/build_release.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def checked_run(command, cwd=None):
    process = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, timeout=180)
    if process.returncode:
        raise RuntimeError(f'Command failed ({process.returncode}): {command}\n{process.stdout[-8000:]}')
    return process.stdout


def snapshots_referenced_by_final_results():
    snapshots = set()
    for relative in ('results/simulation_manifest.json', 'results/harmonised/manifest.json',
                     'results/vintage/manifest.json', 'results/report_manifest.json'):
        manifest = json.loads((ROOT/relative).read_text())
        snapshot = PurePosixPath(manifest['source_snapshot_dir'])
        assert snapshot.parts[:2] == ('results', 'provenance') and len(snapshot.parts) == 3
        assert (ROOT/snapshot).is_dir(), snapshot
        snapshots.add(str(snapshot))
        for path, expected in manifest['source_sha256'].items():
            assert file_sha(ROOT/snapshot/path) == expected, (relative, path, 'snapshot hash')
        assert file_sha(ROOT/snapshot/'docs/analysis_protocol.md') == manifest['protocol_sha256']
        for kind in ('input_sha256', 'output_sha256'):
            for path, expected in manifest.get(kind, {}).items():
                assert file_sha(ROOT/path) == expected, (relative, path, kind)
    return snapshots


def exclusion_reason(relative, snapshots):
    p = PurePosixPath(relative)
    parts = p.parts
    if any(part in {'.git', '.venv', '__pycache__', 'node_modules', 'preview', 'tmp', '.DS_Store'} for part in parts):
        return 'cache, dependency, preview or temporary material'
    if parts[:2] in {('data', 'raw'), ('results', 'initial_runs')}:
        return 'raw source assets or superseded exploratory outputs'
    if relative == 'artifact_tools/repository_command_audit.json':
        return 'local temporary-checkout command log; restoration commands are documented in README/Makefile'
    if parts[:2] == ('data', 'extracted') and p.name != 'extraction_manifest.json':
        return 'third-party documentation text, restored by the download/extraction workflow'
    if parts[:2] == ('results', 'provenance') and '/'.join(parts[:3]) not in snapshots:
        return 'historical snapshot not referenced by the final executed result manifests'
    if parts[0] == 'vintage_data' and p.suffix.lower() not in {'.py', '.json', '.csv', '.txt'}:
        return 'archived raw workbook, document or web-page payload'
    if parts[0] == 'paper':
        if relative in {'paper/main.tex', 'paper/main.bbl', 'paper/references.bib', 'paper/main.pdf'}:
            return None
        if parts[1:2] == ('figures',) and p.suffix == '.pdf':
            return None
        if parts[1:2] == ('tables',) and p.suffix == '.tex':
            return None
        return 'TeX auxiliary file, preview or non-publication artifact'
    if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.html', '.gz', '.pdf', '.zip', '.xlsx', '.ndjson', '.pyc'}:
        return 'raw/full-text/binary preview outside the designated publication artifacts'
    if len(parts) == 1:
        if p.name in {'Makefile', 'LICENSE', '.gitignore', '.gitattributes', 'requirements.txt', 'CITATION.cff'} or p.suffix in {'.md', '.toml', '.yml', '.yaml'}:
            return None
        return 'not an allowlisted repository metadata file'
    if parts[0] not in {'artifact_tools', 'config', 'data', 'data_tools', 'docs', 'experiments', 'results', 'tests', 'vintage_data'}:
        return 'outside the public research component allowlist'
    if p.suffix.lower() not in TEXT_EXTENSIONS:
        return 'unrecognised research artifact type'
    return None


def code_inventory(snapshots):
    entries, excluded = {}, {}
    for base, dirs, files in os.walk(ROOT, followlinks=False):
        base = Path(base)
        for name in list(dirs):
            path = base/name
            relative = path.relative_to(ROOT).as_posix()
            if path.is_symlink() or name in {'node_modules', '__pycache__', '.git', '.venv', 'preview', 'tmp'}:
                excluded[relative+'/'] = 'symlink, dependency, cache or preview directory'
                dirs.remove(name)
        for name in files:
            path = base/name
            relative = path.relative_to(ROOT).as_posix()
            reason = 'symlink' if path.is_symlink() else exclusion_reason(relative, snapshots)
            if reason:
                excluded[relative] = reason
            else:
                entries[relative] = path.read_bytes()
    missing = [path for path in REQUIRED if path not in entries]
    assert not missing, ('Missing mandatory public reproduction files', missing)
    for variant in ('harmonised', 'vintage'):
        for filename in ('manifest.json', 'development_grid.csv', 'selected_hyperparameters.json',
                         'frozen_2025_predictions.csv', 'test_metrics.csv', 'group_test_metrics.csv', 'paired_bootstrap.csv'):
            assert f'results/{variant}/{filename}' in entries
    assert 'results/simulation.csv' in entries and 'results/simulation_stress.csv' in entries
    return entries, excluded


def scan_contents(entries):
    python_files = []
    secret_patterns = [
        re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        re.compile(r'\bsk-[A-Za-z0-9]{32,}\b'),
        re.compile(r'\bwxid_[A-Za-z0-9]+\b'),
        re.compile('xwechat'+'_files/'),
    ]
    for name, data in entries.items():
        suffix = PurePosixPath(name).suffix.lower()
        if suffix not in TEXT_EXTENSIONS and PurePosixPath(name).name not in {'Makefile', 'LICENSE', '.gitignore'}:
            continue
        text = data.decode('utf-8')
        for pattern in secret_patterns:
            assert not pattern.search(text), ('Potential secret/private transfer identifier', name)
        if suffix == '.py':
            ast.parse(text, filename=name)
            python_files.append(name)
    # The source outline lives outside this repository. An allowlist and a
    # private-transfer/key scan complement manual review; neither is a proof
    # against every possible undiscovered sensitive phrase.
    return dict(python_files_syntax_checked=len(python_files), python_files=python_files,
                private_transfer_and_credential_pattern_scan='passed',
                scope='Public research allowlist; original private outline and unrelated workspace never traversed')


def validate_audit_freshness():
    result = json.loads((ROOT/'results/empirical_independent_audit.json').read_text())
    assert result['status'] == 'passed' and result['protected_files_unchanged']
    differences = [name for name, expected in result['input_and_result_sha256'].items()
                   if not (ROOT/name).is_file() or file_sha(ROOT/name) != expected]
    assert not differences, ('Independent empirical audit predates changed files; rerun verifier first', differences)
    assert result['verifier_sha256'] == file_sha(ROOT/'experiments/verify_empirical.py')
    return dict(status='passed', checked_protected_hashes=len(result['input_and_result_sha256']),
                empirical_audit_sha256=file_sha(ROOT/'results/empirical_independent_audit.json'))


def verify_local_document_paths(entries):
    """Check documented local links and script command targets that are literal."""
    checked, external_or_optional = [], []
    for name, data in entries.items():
        if not name.endswith('.md'):
            continue
        text = data.decode()
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.strip('<>').split('#', 1)[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z+.-]*:', target):
                continue
            if target.startswith('/'):
                raise AssertionError(('Nonportable absolute Markdown link', name, target))
            resolved = (ROOT/PurePosixPath(name).parent/target).resolve()
            if resolved.is_relative_to(ROOT):
                relative = resolved.relative_to(ROOT).as_posix()
                if relative in entries or any(p.startswith(relative.rstrip('/')+'/') for p in entries):
                    checked.append([name, target])
                else:
                    external_or_optional.append([name, target])
            else:
                external_or_optional.append([name, target])
    makefile = entries['Makefile'].decode()
    for path in re.findall(r'(?<![\w/])(?:experiments|data_tools|vintage_data|artifact_tools)/[A-Za-z0-9_./-]+\.(?:py|mjs)', makefile):
        assert path in entries, ('Makefile script missing from archive', path)
        checked.append(['Makefile', path])
    # Output/raw-download links can legitimately be absent before recreation;
    # they remain explicitly listed for the release review, never silently
    # treated as if the downloaded asset were shipped.
    return dict(verified_local_links_and_script_targets=checked,
                generated_downloaded_or_external_links_for_review=external_or_optional)


def zip_write(path, entries, prefix=''):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            member = prefix+name
            assert not PurePosixPath(member).is_absolute() and '..' not in PurePosixPath(member).parts
            info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(entries)
        for name, data in entries.items():
            assert archive.read(prefix+name) == data


def pdf_text(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    pages = [' '.join((page.extract_text() or '').split()) for page in reader.pages]
    assert pages and all(pages)
    return pages


def clean_source_compile(archive, canonical, scratch):
    directory = scratch/'source_compile'
    directory.mkdir()
    with zipfile.ZipFile(archive) as source:
        source.extractall(directory)
    assert not (directory/'main.pdf').exists(), 'Source archive must start without a compiled PDF'
    stdout = checked_run(['latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', 'main.tex'], cwd=directory)
    log = (directory/'main.log').read_text(errors='replace')
    failures = [line for line in log.splitlines() if re.search(
        r'^!|LaTeX Error|Undefined control sequence|Citation .*undefined|Reference .*undefined|There were undefined references', line)]
    assert not failures, failures
    layout = [line for line in log.splitlines() if re.search(r'Overfull \\|Underfull \\', line)]
    assert not layout, ('TeX layout warning in clean source build', layout)
    original, rebuilt = pdf_text(canonical), pdf_text(directory/'main.pdf')
    assert original == rebuilt, 'Clean source PDF differs in page count or normalised per-page text'
    # A pixel identity check complements text: source packaging must not alter
    # page geometry. Final editorial visual inspection is still separately
    # performed by the manuscript owner.
    from PIL import Image, ImageChops
    image_directories = []
    for label, path in [('canonical', canonical), ('rebuilt', directory/'main.pdf')]:
        out = scratch/label
        out.mkdir()
        checked_run(['pdftoppm', '-r', '72', '-gray', '-png', str(path), str(out/'page')])
        image_directories.append(out)
    originals, rebuilds = [sorted(p.glob('page-*.png')) for p in image_directories]
    assert len(originals) == len(rebuilds) == len(original)
    for left, right in zip(originals, rebuilds):
        with Image.open(left) as a, Image.open(right) as b:
            assert a.size == b.size and ImageChops.difference(a, b).getbbox() is None, ('Rendered page differs', left.name)
    return dict(status='passed', pages=len(original), normalised_per_page_text_identical=True,
                rendered_pages_pixel_identical=len(original), raster_dpi=72,
                latex_error_count=0, overfull_underfull_warning_count=0,
                canonical_pdf_sha256=file_sha(canonical), rebuilt_pdf_sha256=file_sha(directory/'main.pdf'),
                page_text_sha256=[sha(text.encode()) for text in original],
                latexmk_stdout_sha256=sha(stdout.encode()), latex_log_sha256=sha(log.encode()))


def attach_workbook(entries):
    workbook = DESTINATION/'nhs_wellbeing_results.xlsx'
    if not workbook.exists():
        return None
    manifest = json.loads((ROOT/'artifact_tools/workbook_manifest.json').read_text())
    validation = json.loads((ROOT/'artifact_tools/saved_workbook_validation.json').read_text())
    expected = file_sha(workbook)
    assert expected == manifest['sha256'] == validation['file_sha256']
    assert validation['status'] == 'passed'
    for source in manifest['sources']:
        assert file_sha(ROOT/source['file']) == source['sha256'], ('Workbook input changed', source['file'])
    entries['artifacts/nhs_wellbeing_results.xlsx'] = workbook.read_bytes()
    return dict(path_in_code_archive='nhs_wellbeing_research/artifacts/nhs_wellbeing_results.xlsx',
                sha256=expected, validated_scientific_cells=validation['scientific_cells_compared'])


def standalone_source_release():
    """Permit source validation while repository documentation is finalised."""
    source = {}
    for path in PAPER.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(PAPER).as_posix()
        if (relative in {'main.tex', 'main.bbl', 'references.bib'} or
            relative.startswith('figures/') and path.suffix == '.pdf' or
            relative.startswith('tables/') and path.suffix == '.tex'):
            source[relative] = path.read_bytes()
    assert {'main.tex', 'main.bbl', 'references.bib'} <= set(source)
    protected = {p.name: file_sha(p) for p in DESTINATION.iterdir()
                 if p.is_file() and p.name not in {PACKAGE_NAMES[0], SOURCE_VALIDATION_NAME}}
    with tempfile.TemporaryDirectory(prefix='nhs_source_release_') as temporary:
        scratch = Path(temporary)
        archive = scratch/PACKAGE_NAMES[0]
        zip_write(archive, source)
        result = clean_source_compile(archive, PAPER/'main.pdf', scratch)
        result.update(validated_at_utc=datetime.now(timezone.utc).isoformat(),
                      source_zip_sha256=file_sha(archive), source_members=len(source),
                      builder_sha256=file_sha(__file__),
                      scope='Source archive only; full code archive pending repository finalisation')
        assert all((PAPER/name).read_bytes() == data for name, data in source.items())
        assert protected == {name: file_sha(DESTINATION/name) for name in protected}
        staged = DESTINATION/(PACKAGE_NAMES[0]+'.tmp')
        shutil.copyfile(archive, staged)
        os.replace(staged, DESTINATION/PACKAGE_NAMES[0])
        (DESTINATION/SOURCE_VALIDATION_NAME).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--finalized', action='store_true', help='Use only after the manuscript owner explicitly declares the PDF final.')
    parser.add_argument('--source-only', action='store_true', help='Build/validate only the frozen TeX source archive while code documentation is finalised.')
    arguments = parser.parse_args()
    if not arguments.finalized:
        parser.error('No archive was created. Wait for explicit PDF finalisation, then pass --finalized.')
    for executable in ('latexmk', 'pdftoppm'):
        assert shutil.which(executable), f'Required tool missing: {executable}'
    assert DESTINATION.is_dir(), DESTINATION
    if arguments.source_only:
        standalone_source_release()
        return
    # Any existing first/second-paper releases remain byte-identical. Do not
    # overwrite their shared SHA256SUMS.txt or bundle_manifest.json.
    own = {*PACKAGE_NAMES, PDF_NAME, MANIFEST_NAME, VALIDATION_NAME, CHECKSUM_NAME}
    protected = {p.name: file_sha(p) for p in DESTINATION.iterdir() if p.is_file() and p.name not in own}
    audit = validate_audit_freshness()
    snapshots = snapshots_referenced_by_final_results()
    entries, excluded = code_inventory(snapshots)
    workbook = attach_workbook(entries)
    scans = scan_contents(entries)
    paths = verify_local_document_paths(entries)
    source = {name.removeprefix('paper/'): data for name, data in entries.items()
              if name.startswith('paper/') and name != 'paper/main.pdf'}
    assert {'main.tex', 'main.bbl', 'references.bib'} <= set(source)
    assert any(name.startswith('figures/') for name in source)
    original_input_hashes = {name: sha(data) for name, data in entries.items() if not name.startswith('artifacts/')}
    with tempfile.TemporaryDirectory(prefix='nhs_release_') as temp:
        scratch = Path(temp)
        zip_write(scratch/PACKAGE_NAMES[0], source)
        prior_source_check = DESTINATION/SOURCE_VALIDATION_NAME
        cached = json.loads(prior_source_check.read_text()) if prior_source_check.exists() else {}
        if (cached.get('status') == 'passed' and
            cached.get('canonical_pdf_sha256') == file_sha(PAPER/'main.pdf') and
            cached.get('source_zip_sha256') == file_sha(scratch/PACKAGE_NAMES[0])):
            compilation = dict(cached, reused_identical_source_and_pdf_validation=True)
        else:
            compilation = clean_source_compile(scratch/PACKAGE_NAMES[0], PAPER/'main.pdf', scratch)
        zip_write(scratch/PACKAGE_NAMES[1], entries, 'nhs_wellbeing_research/')
        (scratch/PDF_NAME).write_bytes(entries['paper/main.pdf'])
        # Final race check: no file should change after finalisation/inventory.
        assert all(file_sha(ROOT/name) == expected for name, expected in original_input_hashes.items()), 'Repository changed during release assembly'
        assert protected == {name: file_sha(DESTINATION/name) for name in protected}, 'Unrelated existing release changed'
        validation = dict(status='passed', validated_at_utc=datetime.now(timezone.utc).isoformat(),
            independent_empirical_audit=audit, source_compile=compilation,
            code_syntax_and_content_scan=scans, reproduction_path_checks=paths,
            final_provenance_snapshots=sorted(snapshots), bundled_workbook=workbook,
            code_archive_members=len(entries), source_archive_members=len(source),
            unrelated_release_files_preserved=len(protected),
            scope='Packaging verification only; no scientific reruns, submission or publication performed')
        (scratch/VALIDATION_NAME).write_text(json.dumps(validation, indent=2)+'\n')
        if (DESTINATION/SOURCE_VALIDATION_NAME).exists():
            shutil.copyfile(DESTINATION/SOURCE_VALIDATION_NAME, scratch/SOURCE_VALIDATION_NAME)
        artifacts = {name: dict(sha256=file_sha(scratch/name), bytes=(scratch/name).stat().st_size)
                     for name in (*PACKAGE_NAMES, PDF_NAME, VALIDATION_NAME)}
        if (scratch/SOURCE_VALIDATION_NAME).exists():
            artifacts[SOURCE_VALIDATION_NAME] = dict(sha256=file_sha(scratch/SOURCE_VALIDATION_NAME),
                                                    bytes=(scratch/SOURCE_VALIDATION_NAME).stat().st_size)
        manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
            builder_sha256=file_sha(__file__), artifacts=artifacts,
            source_archive_members={name: dict(sha256=sha(data), bytes=len(data)) for name, data in sorted(source.items())},
            code_archive_members={name: dict(sha256=sha(data), bytes=len(data)) for name, data in sorted(entries.items())},
            exclusions=excluded, public_bundle_root='nhs_wellbeing_research/',
            timestamps='Execution/provenance timestamps retained; deterministic archive headers are not experiment dates')
        (scratch/MANIFEST_NAME).write_text(json.dumps(manifest, indent=2)+'\n')
        names = [*PACKAGE_NAMES, PDF_NAME, VALIDATION_NAME, MANIFEST_NAME]
        checksum_names = names+([SOURCE_VALIDATION_NAME] if (scratch/SOURCE_VALIDATION_NAME).exists() else [])
        checksums = ''.join(f'{file_sha(scratch/name)}  {name}\n' for name in checksum_names)
        (scratch/CHECKSUM_NAME).write_text(checksums)
        # All validation precedes publication of the completed local artifacts.
        for name in [*names, CHECKSUM_NAME]:
            staged = DESTINATION/(name+'.tmp')
            shutil.copyfile(scratch/name, staged)
            os.replace(staged, DESTINATION/name)
    assert protected == {name: file_sha(DESTINATION/name) for name in protected}
    print(json.dumps(dict(status='passed', artifacts={name: str(DESTINATION/name) for name in own},
                         code_members=len(entries), source_members=len(source), pages=compilation['pages']), indent=2))


if __name__ == '__main__':
    main()
