"""Google Test 결과 파서 (`--gtest_output=xml:` 또는 `json:`)."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ..models import TestCase, TestSet


def _to_float(value) -> float:
    try:
        return float(str(value).rstrip("s"))
    except (TypeError, ValueError):
        return 0.0


def _parse_xml(path: Path, name: str) -> TestSet:
    root = ET.parse(path).getroot()
    result = TestSet(name=name, timestamp=root.get("timestamp", ""), source=str(path))
    for suite in root.iter("testsuite"):
        suite_name = suite.get("name", "(suite)")
        for case in suite.findall("testcase"):
            failures = case.findall("failure")
            skipped = case.find("skipped") is not None or case.get("result") == "skipped" \
                or case.get("status") == "notrun"
            message = ""
            if failures:
                status = "failed"
                message = "\n".join((f.get("message", "") or (f.text or "")).strip() for f in failures)
            elif skipped:
                status = "skipped"
            else:
                status = "passed"
            result.cases.append(TestCase(suite_name, case.get("name", "(case)"), status,
                                         _to_float(case.get("time")), message))
    return result


def _parse_json(path: Path, name: str) -> TestSet:
    data = json.loads(path.read_text(encoding="utf-8"))
    result = TestSet(name=name, timestamp=data.get("timestamp", ""), source=str(path))
    for suite in data.get("testsuites", []):
        suite_name = suite.get("name", "(suite)")
        for case in suite.get("testsuite", []):
            failures = case.get("failures") or []
            res = str(case.get("result", "")).upper()
            if failures:
                status, message = "failed", "\n".join(str(f.get("failure", "")).strip() for f in failures)
            elif res in ("SKIPPED", "SUPPRESSED") or str(case.get("status", "")).upper() == "NOTRUN":
                status, message = "skipped", ""
            else:
                status, message = "passed", ""
            result.cases.append(TestCase(suite_name, case.get("name", "(case)"), status,
                                         _to_float(case.get("time")), message))
    return result


def parse_gtest(path: str, name: str = "tests") -> TestSet:
    p = Path(path)
    head = p.read_text(encoding="utf-8", errors="replace").lstrip()[:1]
    return _parse_json(p, name) if head == "{" else _parse_xml(p, name)
