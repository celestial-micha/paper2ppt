"""Utilities for benchmark paper manifests."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_MANIFEST = Path("benchmarks") / "papers.json"


def load_manifest(path: Path = DEFAULT_MANIFEST) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expand_paper_set(manifest: Dict[str, Any], set_name: str) -> List[Dict[str, Any]]:
    """Return papers for a set, expanding any included sets."""
    sets = manifest.get("sets", {})
    if set_name not in sets:
        raise KeyError(f"Unknown paper set: {set_name}")
    item = sets[set_name]
    papers: List[Dict[str, Any]] = []
    for included in item.get("includes", []):
        papers.extend(expand_paper_set(manifest, included))
    papers.extend(item.get("papers", []))
    papers.extend(item.get("additional_papers", []))
    return papers


def validate_paper_files(manifest_path: Path = DEFAULT_MANIFEST, set_name: str = "local_12") -> Dict[str, Any]:
    manifest = load_manifest(manifest_path)
    papers = expand_paper_set(manifest, set_name)
    missing = []
    present = []
    for paper in papers:
        path = Path(paper.get("path", ""))
        record = {
            "id": paper.get("id", ""),
            "path": str(path),
            "source_url": paper.get("source_url", ""),
        }
        if path.exists() and path.stat().st_size > 0:
            present.append({**record, "bytes": path.stat().st_size})
        else:
            missing.append(record)
    return {
        "set": set_name,
        "total": len(papers),
        "present": present,
        "missing": missing,
    }


def download_missing_papers(
    manifest_path: Path = DEFAULT_MANIFEST,
    set_name: str = "ai20",
    verbose: bool = False,
) -> Dict[str, Any]:
    manifest = load_manifest(manifest_path)
    papers = expand_paper_set(manifest, set_name)
    downloaded = []
    skipped = []
    failed = []
    for paper in papers:
        path = Path(paper.get("path", ""))
        url = paper.get("source_url", "")
        if path.exists() and path.stat().st_size > 0:
            _log(f"SKIP {paper.get('id', '')}: {path} already exists", verbose)
            skipped.append({"id": paper.get("id", ""), "path": str(path), "reason": "already exists"})
            continue
        if not url:
            _log(f"SKIP {paper.get('id', '')}: no source_url", verbose)
            skipped.append({"id": paper.get("id", ""), "path": str(path), "reason": "no source_url"})
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _log(f"DOWNLOAD {paper.get('id', '')}: {url}", verbose)
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "paper2ppt-benchmark/1.0"},
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                with path.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
            _log(f"DONE {paper.get('id', '')}: {path} ({path.stat().st_size} bytes)", verbose)
            downloaded.append({"id": paper.get("id", ""), "path": str(path), "bytes": path.stat().st_size})
        except Exception as exc:
            if path.exists() and path.stat().st_size == 0:
                path.unlink()
            _log(f"FAIL {paper.get('id', '')}: {exc}", verbose)
            failed.append({"id": paper.get("id", ""), "path": str(path), "url": url, "error": str(exc)})
    return {
        "set": set_name,
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed,
    }


def _log(message: str, enabled: bool) -> None:
    if enabled:
        print(message, flush=True)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or download paper2ppt benchmark paper sets.")
    parser.add_argument("action", choices=["validate", "download"])
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--set", default="local_12", dest="set_name")
    parser.add_argument("--quiet", action="store_true", help="Only print final JSON output.")
    args = parser.parse_args(argv)

    print(f"Python: {sys.executable}", flush=True)
    print(f"Action: {args.action}; set: {args.set_name}; manifest: {args.manifest}", flush=True)

    manifest_path = Path(args.manifest)
    if args.action == "validate":
        result = validate_paper_files(manifest_path, args.set_name)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["missing"] else 0

    result = download_missing_papers(manifest_path, args.set_name, verbose=not args.quiet)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
