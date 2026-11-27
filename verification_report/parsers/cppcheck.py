"""CppCheck 결과 파서 (`--xml --xml-version=2`)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Iterable, List

from ..models import Violation
from ..util import norm_path


def parse_cppcheck(path: str, roots: Iterable[str] = ("src", "include", "tests"),
                   strip: Iterable[str] = ()) -> List[Violation]:
    root = ET.parse(path).getroot()
    out: List[Violation] = []
    for err in root.iter("error"):
        loc = err.find("location")
        file = loc.get("file", "") if loc is not None else err.get("file0", "")
        try:
            line = int(loc.get("line", "0")) if loc is not None else 0
        except ValueError:
            line = 0
        out.append(Violation(rule=err.get("id", ""), severity=err.get("severity", "unknown"),
                             message=err.get("msg", "") or err.get("verbose", ""),
                             file=norm_path(file, roots, strip) if file else "(no file)", line=line))
    return out
