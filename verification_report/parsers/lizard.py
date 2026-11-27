"""Lizard 결과 파서.

- CSV(`lizard --csv`) 권장: 함수 라인수(length)까지 있다.
- XML(`lizard --xml`)도 읽지만 함수 라인수(length)가 없어 NCSS 로 대신하며 추정값으로 표시한다.
"""
from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, List

from ..models import LizardFunction
from ..util import norm_path


def _int(value, default=0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _parse_csv(path: Path, roots, strip) -> List[LizardFunction]:
    out: List[LizardFunction] = []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            # NLOC, CCN, token, PARAM, length, location, file, function, long_name, start, end
            if len(row) < 11 or not row[0].strip().isdigit():
                continue
            out.append(LizardFunction(name=row[7], file=norm_path(row[6], roots, strip),
                                      start=_int(row[9]), end=_int(row[10]), nloc=_int(row[0]),
                                      ccn=_int(row[1]), length=_int(row[4]), params=_int(row[3])))
    return out


def _parse_xml(path: Path, roots, strip) -> List[LizardFunction]:
    out: List[LizardFunction] = []
    root = ET.parse(path).getroot()
    for measure in root.iter("measure"):
        if measure.get("type") != "Function":
            continue
        labels = [(lb.text or "").strip() for lb in measure.findall("./labels/label")]
        for item in measure.findall("item"):
            values = [_int(v.text) for v in item.findall("value")]
            row = dict(zip(labels, values))
            label = item.get("name", "")
            func, _, where = label.rpartition(" at ")
            file, _, line = where.rpartition(":")
            start = _int(line)
            nloc = row.get("NCSS", 0)
            out.append(LizardFunction(name=func or label, file=norm_path(file, roots, strip), start=start,
                                      end=start + max(nloc - 1, 0), nloc=nloc, ccn=row.get("CCN", 0),
                                      length=nloc, length_estimated=True))
    return out


def parse_lizard(path: str, roots: Iterable[str] = ("src", "include", "tests"),
                 strip: Iterable[str] = ()) -> List[LizardFunction]:
    p = Path(path)
    head = p.read_text(encoding="utf-8", errors="replace").lstrip()[:1]
    funcs = _parse_xml(p, roots, strip) if head == "<" else _parse_csv(p, roots, strip)
    funcs.sort(key=lambda f: (f.file, f.start))
    return funcs
