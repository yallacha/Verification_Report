"""LLVM 커버리지 파서 (`llvm-cov export` JSON).

- `-summary-only` JSON(`ci/quality.sh` 가 만드는 summary.json): 총괄과 파일 단위.
- 전체 export JSON(`-summary-only` 없이): 함수 단위(실행 횟수, region, branch)까지.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Optional

from ..models import CovFile, CovFunction, CovMetric, CovSet
from ..util import norm_path

METRIC_KEYS = ("lines", "functions", "regions", "branches", "mcdc")
CODE_REGION = 0


def _metrics(summary: Dict) -> Dict[str, CovMetric]:
    out: Dict[str, CovMetric] = {}
    for key in METRIC_KEYS:
        item = summary.get(key)
        if isinstance(item, dict) and "count" in item:
            out[key] = CovMetric(int(item.get("covered", 0)), int(item["count"]))
    return out


def _function(raw: Dict, roots: Iterable[str], strip: Iterable[str]) -> Optional[CovFunction]:
    filenames = raw.get("filenames") or []
    if not filenames:
        return None
    code = [r for r in raw.get("regions", []) if len(r) >= 8 and r[7] == CODE_REGION and r[5] == 0]
    regions = CovMetric(sum(1 for r in code if r[4] > 0), len(code)) if code else None
    branches = None
    raw_branches = [b for b in raw.get("branches", []) if len(b) >= 6]
    if raw_branches:
        branches = CovMetric(sum((b[4] > 0) + (b[5] > 0) for b in raw_branches), 2 * len(raw_branches))
    line = code[0][0] if code else 0
    return CovFunction(name=raw.get("name", "(function)"),
                       file=norm_path(filenames[0], roots, strip), line=line,
                       count=int(raw.get("count", 0)), regions=regions, branches=branches)


def parse_llvm_cov(path: str, name: str = "coverage", roots: Iterable[str] = ("src", "include", "tests"),
                   strip: Iterable[str] = ()) -> CovSet:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))["data"][0]
    result = CovSet(name=name, source=str(p), totals=_metrics(data.get("totals", {})))
    by_path: Dict[str, CovFile] = {}
    for raw in data.get("files", []):
        cov_file = CovFile(path=norm_path(raw["filename"], roots, strip), metrics=_metrics(raw.get("summary", {})))
        by_path[cov_file.path] = cov_file
        result.files.append(cov_file)
    for raw in data.get("functions", []):
        func = _function(raw, roots, strip)
        if func is None:
            continue
        result.has_functions = True
        target = by_path.get(func.file)
        if target is None:
            target = CovFile(path=func.file)
            by_path[func.file] = target
            result.files.append(target)
        target.functions.append(func)
    for cov_file in result.files:
        cov_file.functions.sort(key=lambda f: (f.line, f.name))
    result.files.sort(key=lambda f: f.path)
    return result
