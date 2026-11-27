"""검증 결과 데이터 모델."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TestCase:
    suite: str
    name: str
    status: str  # passed | failed | skipped
    time: float = 0.0
    message: str = ""


@dataclass
class TestSet:
    name: str
    cases: List[TestCase] = field(default_factory=list)
    timestamp: str = ""
    source: str = ""

    def count(self, status: str) -> int:
        return sum(1 for c in self.cases if c.status == status)

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed(self) -> int:
        return self.count("passed")

    @property
    def failed(self) -> int:
        return self.count("failed")

    @property
    def skipped(self) -> int:
        return self.count("skipped")

    @property
    def duration(self) -> float:
        return sum(c.time for c in self.cases)

    @property
    def pass_rate(self) -> float:
        executed = self.passed + self.failed
        return 100.0 if executed == 0 else 100.0 * self.passed / executed


@dataclass
class CovMetric:
    covered: int
    count: int

    @property
    def percent(self) -> float:
        # 대상 항목이 0개이면 100% 로 본다 (ci/check_coverage.py 와 같은 규칙).
        return 100.0 if self.count == 0 else 100.0 * self.covered / self.count


@dataclass
class CovFunction:
    name: str
    file: str
    line: int
    count: int  # 실행 횟수
    regions: Optional[CovMetric] = None
    branches: Optional[CovMetric] = None


@dataclass
class CovFile:
    path: str
    metrics: Dict[str, CovMetric] = field(default_factory=dict)
    functions: List[CovFunction] = field(default_factory=list)


@dataclass
class CovSet:
    name: str
    files: List[CovFile] = field(default_factory=list)
    totals: Dict[str, CovMetric] = field(default_factory=dict)
    has_functions: bool = False
    source: str = ""


@dataclass
class Violation:
    rule: str
    severity: str
    message: str
    file: str
    line: int
    function: str = ""


@dataclass
class LizardFunction:
    name: str
    file: str
    start: int
    end: int
    nloc: int
    ccn: int
    length: int
    params: int = 0
    length_estimated: bool = False


@dataclass
class BuildInfo:
    title: str = "Verification Report"
    build_id: str = ""
    build_time: str = ""
    branch: str = ""
    commit: str = ""
    generated_at: str = ""
