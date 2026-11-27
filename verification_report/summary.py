"""판정 기준(게이트)을 적용해 도구별 총괄 결과를 만든다. 기준은 Claude_Clang `CLAUDE.md` 2장과 같다."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .models import BuildInfo, CovSet, LizardFunction, TestSet, Violation
from .util import fmt_pct

# 커버리지 게이트 기본값: 세트 이름 -> (지표, 최소 %).  CLAUDE.md: 단위 MC/DC 100%, 통합 함수 100%.
DEFAULT_GATES: Dict[str, Tuple[str, float]] = {"unit": ("mcdc", 100.0), "integration": ("functions", 100.0)}

STATUS_LABEL = {"pass": "PASS", "fail": "FAIL", "na": "N/A"}


@dataclass
class Row:
    scope: str      # 세트 이름 등
    metric: str
    value: str
    gate: str
    status: str     # pass | fail | na


@dataclass
class ToolResult:
    key: str        # gtest | coverage | cppcheck | lizard
    title: str
    status: str
    headline: str
    sub: str = ""
    rows: List[Row] = field(default_factory=list)
    page: str = ""


@dataclass
class Report:
    build: BuildInfo
    tests: List[TestSet] = field(default_factory=list)
    coverage: List[CovSet] = field(default_factory=list)
    cppcheck: Optional[List[Violation]] = None
    lizard: Optional[List[LizardFunction]] = None
    gates: Dict[str, Tuple[str, float]] = field(default_factory=lambda: dict(DEFAULT_GATES))
    max_ccn: int = 10
    max_length: int = 80

    def lizard_reasons(self, func: LizardFunction) -> List[str]:
        reasons = []
        if func.ccn > self.max_ccn:
            reasons.append(f"CCN {func.ccn} > {self.max_ccn}")
        if func.length > self.max_length:
            reasons.append(f"라인수 {func.length} > {self.max_length}")
        return reasons

    def lizard_violations(self) -> List[LizardFunction]:
        return [f for f in (self.lizard or []) if self.lizard_reasons(f)]

    def resolve_functions(self) -> None:
        """CppCheck 위반의 파일:줄을 Lizard 함수 범위와 대조해 함수 이름을 채운다."""
        if not self.cppcheck or not self.lizard:
            return
        by_file: Dict[str, List[LizardFunction]] = {}
        for func in self.lizard:
            by_file.setdefault(func.file, []).append(func)
        for v in self.cppcheck:
            for func in by_file.get(v.file, []):
                if func.start <= v.line <= max(func.end, func.start):
                    v.function = func.name
                    break


def coverage_gate(report: Report, cov: CovSet) -> Optional[Tuple[str, float]]:
    return report.gates.get(cov.name)


def evaluate(report: Report) -> List[ToolResult]:
    results: List[ToolResult] = []

    # Google Test
    if report.tests:
        rows, failed_any = [], False
        total = sum(t.total for t in report.tests)
        failed = sum(t.failed for t in report.tests)
        for t in report.tests:
            ok = t.total > 0 and t.failed == 0
            failed_any |= not ok
            rows.append(Row(t.name, "성공률", f"{t.passed}/{t.passed + t.failed} ({fmt_pct(t.pass_rate)})",
                            "100%", "pass" if ok else "fail"))
        status = "fail" if failed_any else "pass"
        results.append(ToolResult("gtest", "Google Test", status, f"{total - failed}/{total} 통과",
                                  f"실패 {failed}건", rows, "gtest.html"))
    else:
        results.append(ToolResult("gtest", "Google Test", "na", "입력 없음", "", [], "gtest.html"))

    # LLVM 커버리지
    if report.coverage:
        rows, failed_any = [], False
        for cov in report.coverage:
            gate = coverage_gate(report, cov)
            for key in ("lines", "functions", "regions", "branches", "mcdc"):
                metric = cov.totals.get(key)
                if metric is None:
                    continue
                is_gate = gate is not None and gate[0] == key
                ok = metric.percent >= gate[1] if is_gate else True
                failed_any |= not ok
                rows.append(Row(cov.name, key, f"{fmt_pct(metric.percent)} ({metric.covered}/{metric.count})",
                                f"≥ {gate[1]:g}%" if is_gate else "-", ("pass" if ok else "fail") if is_gate else "na"))
            if gate is not None and gate[0] not in cov.totals:
                failed_any = True
                rows.append(Row(cov.name, gate[0], "측정값 없음", f"≥ {gate[1]:g}%", "fail"))
        first = report.coverage[0]
        main = first.totals.get("lines") or next(iter(first.totals.values()), None)
        headline = f"{first.name} 라인 {fmt_pct(main.percent)}" if main else "측정값 없음"
        results.append(ToolResult("coverage", "LLVM 커버리지", "fail" if failed_any else "pass", headline,
                                  f"세트 {len(report.coverage)}개", rows, "coverage.html"))
    else:
        results.append(ToolResult("coverage", "LLVM 커버리지", "na", "입력 없음", "", [], "coverage.html"))

    # CppCheck
    if report.cppcheck is not None:
        n = len(report.cppcheck)
        results.append(ToolResult("cppcheck", "CppCheck", "pass" if n == 0 else "fail", f"위반 {n}건",
                                  "기준: 0건",
                                  [Row("src", "위반 수", str(n), "0", "pass" if n == 0 else "fail")], "cppcheck.html"))
    else:
        results.append(ToolResult("cppcheck", "CppCheck", "na", "입력 없음", "", [], "cppcheck.html"))

    # Lizard
    if report.lizard is not None:
        bad = report.lizard_violations()
        ccn_n = sum(1 for f in report.lizard if f.ccn > report.max_ccn)
        len_n = sum(1 for f in report.lizard if f.length > report.max_length)
        rows = [
            Row("src", f"순환복잡도 > {report.max_ccn}", f"{ccn_n}개 함수", "0", "pass" if ccn_n == 0 else "fail"),
            Row("src", f"함수 라인수 > {report.max_length}", f"{len_n}개 함수", "0", "pass" if len_n == 0 else "fail"),
        ]
        results.append(ToolResult("lizard", "Lizard", "pass" if not bad else "fail", f"초과 함수 {len(bad)}개",
                                  f"전체 {len(report.lizard)}개 함수 중", rows, "lizard.html"))
    else:
        results.append(ToolResult("lizard", "Lizard", "na", "입력 없음", "", [], "lizard.html"))
    return results


def overall_status(results: List[ToolResult]) -> str:
    present = [r for r in results if r.status != "na"]
    if not present:
        return "na"
    return "fail" if any(r.status == "fail" for r in present) else "pass"
