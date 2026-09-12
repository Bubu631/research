#!/usr/bin/env python3
"""Build local research archives without publishing or assigning a license."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKIP_SUFFIXES = {".aux", ".log", ".out", ".blg", ".fls", ".pyc", ".fdb_latexmk"}


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            result.update(block)
    return result.hexdigest()


def portable(path):
    relative = path.relative_to(ROOT)
    return (not any(p in {".venv", ".cache", "__pycache__", ".git"} for p in relative.parts)
            and path.suffix not in SKIP_SUFFIXES
            and not path.name.endswith(".synctex.gz")
            and path.name != ".DS_Store")


def gradient_evidence(path):
    return path.name.startswith("public_gradients_") and path.suffix == ".npz"


def write_archive(destination, entries):
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, relative in entries:
            archive.write(path, str(relative))
    with zipfile.ZipFile(destination) as archive:
        damaged = archive.testzip()
        if damaged:
            raise RuntimeError(f"Corrupt archive member: {damaged}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent/"output/release")
    args = parser.parse_args()
    destination = args.output.resolve()
    if ROOT == destination or ROOT in destination.parents:
        raise ValueError("Output directory must be outside the release source tree.")
    destination.mkdir(parents=True, exist_ok=True)
    native = json.loads((ROOT/"papers/edit_localization/results/full_parameter/manifest.json").read_text())
    if not native.get("completed"):
        raise RuntimeError("Refusing to package unfinished native-gradient evidence.")
    for paper in ["edit_localization", "base_upgrade"]:
        base = ROOT/"papers"/paper
        sources = sorted(p for p in base.rglob("*") if p.is_file()
                         and (p.suffix in {".tex", ".bib", ".bbl", ".sty", ".bst"}
                              or ("figures" in p.parts and p.suffix == ".pdf")))
        write_archive(destination/(paper+"_source.zip"), [(p,p.relative_to(base)) for p in sources])
        shutil.copyfile(base/"main.pdf", destination/(paper+"_paper.pdf"))
    shutil.copyfile(destination/"edit_localization_source.zip", destination/"edit_localization_4authors_source.zip")
    shutil.copyfile(destination/"edit_localization_paper.pdf", destination/"edit_localization_4authors_paper.pdf")
    shutil.copyfile(destination/"base_upgrade_source.zip", destination/"base_upgrade_3authors_source.zip")
    shutil.copyfile(destination/"base_upgrade_paper.pdf", destination/"base_upgrade_3authors_paper.pdf")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and portable(p))
    write_archive(destination/"research_code_and_papers.zip",
                  [(p,Path("research_release")/p.relative_to(ROOT)) for p in files if not gradient_evidence(p)])
    write_archive(destination/"public_gradient_evidence.zip",
                  [(p,Path("research_release")/p.relative_to(ROOT)) for p in files if gradient_evidence(p)])
    generated_names = ["edit_localization_source.zip", "base_upgrade_source.zip",
                       "edit_localization_paper.pdf", "base_upgrade_paper.pdf",
                       "research_code_and_papers.zip", "public_gradient_evidence.zip",
                       "edit_localization_4authors_source.zip", "edit_localization_4authors_paper.pdf",
                       "base_upgrade_3authors_source.zip", "base_upgrade_3authors_paper.pdf"]
    packages = {name:dict(bytes=(destination/name).stat().st_size, sha256=sha(destination/name))
                for name in generated_names}
    authorship = json.loads((ROOT/"paper_authorship.json").read_text())
    note = dict(status="Local research manuscripts and reproducibility packages; publication status is not verified by this manifest",
                authors_by_paper=authorship["authors_by_paper"],
                affiliations_by_author=authorship["affiliations_by_author"],
                code_archive="Omits large per-record vocabulary gradients; all figures and summary results included",
                evidence_archive="Contains omitted per-record gradients in matching repository paths",
                excluded="Private interview materials, original attachments, model/data download caches, native mean-gradient bank",
                sources="Compilable LaTeX manuscripts with author-confirmed name and affiliation; publication license remains to be selected",
                packages=packages)
    (destination/"bundle_manifest.json").write_text(json.dumps(note,indent=2)+"\n")
    (destination/"SHA256SUMS.txt").write_text("".join(f"{r['sha256']}  {name}\n" for name,r in packages.items()))
    print(json.dumps(note,indent=2))


if __name__ == "__main__":
    main()
