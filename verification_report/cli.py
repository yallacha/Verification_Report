"""명령행 인터페이스: 도구별 결과 파일을 읽어 HTML 리포트를 만든다."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import List, Optional, Tuple

from .models import BuildInfo
from .parsers import parse_cppcheck, parse_gtest, parse_lizard, parse_llvm_cov
from .render import write_report
from .summary import DEFAULT_GATES, Report


def _named(value: str, default: str) -> Tuple[str, str]:
    """`이름=경로` 또는 `경로` 를 (이름, 경로) 로 나눈다. 윈도 드라이브 문자(C:\\)와 구분한다."""
    name, sep, path = value.partition("=")
    if sep and len(name) > 1:
        return name, path
    return default, value


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="verification_report", description="검증 결과 HTML 대시보드 생성기")
    p.add_argument("--gtest", action="append", default=[], metavar="[이름=]경로",
                   help="Google Test XML/JSON. 여러 번 지정 가능 (예: unit=build/reports/unit/test-results.xml)")
    p.add_argument("--coverage", action="append", default=[], metavar="[이름=]경로",
                   help="llvm-cov export JSON. 여러 번 지정 가능 (함수 단위는 -summary-only 없는 export 필요)")
    p.add_argument("--cppcheck", metavar="경로", help="CppCheck XML (--xml-version=2)")
    p.add_argument("--lizard", metavar="경로", help="Lizard CSV(권장) 또는 XML")
    p.add_argument("--out", default="report", help="출력 디렉터리 (기본: report)")
    p.add_argument("--title", default="Verification Report")
    p.add_argument("--build-id", default="")
    p.add_argument("--build-time", default="", help="빌드 일시 (기본: 지금)")
    p.add_argument("--branch", default="")
    p.add_argument("--commit", default="")
    p.add_argument("--max-ccn", type=int, default=10, help="순환복잡도 기준 (기본 10)")
    p.add_argument("--max-length", type=int, default=80, help="함수 라인수 기준 (기본 80)")
    p.add_argument("--gate", action="append", default=[], metavar="세트:지표:최소%",
                   help="커버리지 판정 기준. 기본 unit:mcdc:100, integration:functions:100. 예: unit:mcdc:100")
    p.add_argument("--source-root", action="append", default=[],
                   help="경로에서 제거할 접두어(예: /work/). 여러 번 지정 가능")
    p.add_argument("--root-dir", action="append", default=[],
                   help="저장소 기준 경로의 시작 디렉터리 이름 (기본: src include tests)")
    p.add_argument("--fail-on-violation", action="store_true", help="기준 미달이면 종료 코드 1 (CI 용)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    roots = tuple(args.root_dir) or ("src", "include", "tests")
    strip = tuple(args.source_root)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = Report(build=BuildInfo(title=args.title, build_id=args.build_id, build_time=args.build_time or now,
                                    branch=args.branch, commit=args.commit, generated_at=now),
                    max_ccn=args.max_ccn, max_length=args.max_length)
    report.gates = dict(DEFAULT_GATES)
    for spec in args.gate:
        try:
            name, metric, minimum = spec.split(":")
            report.gates[name] = (metric, float(minimum))
        except ValueError:
            print(f"오류: --gate 형식은 세트:지표:최소% 입니다 ({spec})", file=sys.stderr)
            return 2
    try:
        for i, value in enumerate(args.gtest):
            name, path = _named(value, "tests" if len(args.gtest) == 1 else f"tests{i + 1}")
            report.tests.append(parse_gtest(path, name))
        for i, value in enumerate(args.coverage):
            name, path = _named(value, "coverage" if len(args.coverage) == 1 else f"coverage{i + 1}")
            report.coverage.append(parse_llvm_cov(path, name, roots, strip))
        if args.cppcheck:
            report.cppcheck = parse_cppcheck(args.cppcheck, roots, strip)
        if args.lizard:
            report.lizard = parse_lizard(args.lizard, roots, strip)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print(f"오류: 결과 파일을 읽을 수 없습니다: {exc!r}", file=sys.stderr)
        return 2
    except Exception as exc:  # XML/JSON 파싱 오류
        print(f"오류: 결과 파일 형식이 올바르지 않습니다: {exc!r}", file=sys.stderr)
        return 2
    written = write_report(report, args.out)
    print(f"리포트 생성: {written[0].parent / 'index.html'}")
    if args.fail_on_violation:
        from .summary import evaluate, overall_status
        return 1 if overall_status(evaluate(report)) == "fail" else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
