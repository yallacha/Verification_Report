"""HTML 렌더링: 대시보드(index.html)와 도구별 상세 페이지."""
from __future__ import annotations

from collections import OrderedDict
from html import escape as h
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import charts
from .assets import CSS, JS
from .models import CovFile, CovMetric, CovSet, LizardFunction, TestSet, Violation
from .summary import STATUS_LABEL, Report, ToolResult, coverage_gate, evaluate, overall_status
from .util import fmt_pct, module_of

PAGES = [("index.html", "대시보드", None), ("gtest.html", "Google Test", "gtest"),
         ("coverage.html", "LLVM 커버리지", "coverage"), ("cppcheck.html", "CppCheck", "cppcheck"),
         ("lizard.html", "Lizard", "lizard")]
SEVERITIES = ["error", "warning", "style", "performance", "portability", "information"]


# --------------------------------------------------------------------------- 공통 조각
def badge(status: str) -> str:
    return f'<span class="badge {status}">{STATUS_LABEL.get(status, status)}</span>'


def row_badge(status: str) -> str:
    # 기준이 없는 지표(보고용)는 판정 대신 '참고'로 표시한다.
    return badge(status) if status != "na" else '<span class="badge na">참고</span>'


def page(report: Report, results: List[ToolResult], current: str, title: str, body: str) -> str:
    status = {r.page: r.status for r in results}
    links = []
    for href, label, _ in PAGES:
        cur = ' aria-current="page"' if href == current else ""
        dot = f'<span class="dot {status[href]}"></span>' if href in status and status[href] != "na" else ""
        links.append(f'<a href="{href}"{cur}>{dot}{h(label)}</a>')
    return (f'<!doctype html>\n<html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{h(title)} — {h(report.build.title)}</title><style>{CSS}</style></head><body>'
            f'<nav class="top"><div class="wrap">{"".join(links)}</div></nav>'
            f'<div class="wrap">{body}'
            f'<footer>리포트 생성: {h(report.build.generated_at)}</footer></div>'
            f'<script>{JS}</script></body></html>\n')


def build_chips(report: Report) -> str:
    b = report.build
    items = [("빌드 일시", b.build_time), ("빌드 번호", b.build_id), ("브랜치", b.branch), ("커밋", b.commit)]
    return '<div class="chips">' + "".join(f'<span class="chip">{k} <b>{h(v)}</b></span>' for k, v in items if v) + "</div>"


def page_header(report: Report, title: str, subtitle: str = "") -> str:
    sub = f'<p class="note">{h(subtitle)}</p>' if subtitle else ""
    return f'<header class="page"><h1>{h(title)}</h1>{build_chips(report)}{sub}</header>'


def table(headers: Sequence[Tuple[str, str]], rows: Sequence[str]) -> str:
    head = "".join(f'<th class="{c}">{h(t)}</th>' for t, c in headers)
    return f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def toolbar(bad_label: str, bad_checked: bool = False) -> str:
    chk = " checked" if bad_checked else ""
    return ('<div class="toolbar"><input id="q" type="search" placeholder="모듈·파일·함수 검색" aria-label="검색">'
            f'<label><input id="bad" type="checkbox"{chk}> {h(bad_label)}</label>'
            '<button type="button" data-expand="all">모두 펼치기</button>'
            '<button type="button" data-expand="none">모두 접기</button></div>')


def pill(text: str, cls: str = "") -> str:
    return f'<span class="pill {cls}">{h(text)}</span>'


def details(kind: str, name: str, pills: str, inner: str, q: str, bad: bool, level: str, opened: bool = False) -> str:
    return (f'<details class="{level}" data-q="{h(q.lower())}" data-bad="{int(bad)}"{" open" if opened else ""}>'
            f'<summary><span class="name"><span class="kind">{kind}</span>{h(name)}</span>{pills}</summary>'
            f'<div class="inner">{inner}</div></details>')


def group_by_module(items, path_of: Callable) -> "OrderedDict[str, OrderedDict[str, list]]":
    tree: "OrderedDict[str, OrderedDict[str, list]]" = OrderedDict()
    for item in sorted(items, key=lambda i: path_of(i)):
        path = path_of(item)
        tree.setdefault(module_of(path), OrderedDict()).setdefault(path, []).append(item)
    return tree


# --------------------------------------------------------------------------- 대시보드
def _gtest_card(report: Report, r: ToolResult) -> str:
    sets = report.tests
    if not sets:
        return ""
    p, f, s = sum(t.passed for t in sets), sum(t.failed for t in sets), sum(t.skipped for t in sets)
    total = p + f
    center = "100%" if total == 0 else f"{100.0 * p / total:.1f}%".replace(".0%", "%")
    chart = charts.donut([("통과", p, "pass"), ("실패", f, "fail"), ("건너뜀", s, "skip")], center, "성공률")
    legend = ('<div class="legend"><span><i style="background:var(--pass)"></i>통과 {}</span>'
              '<span><i style="background:var(--fail)"></i>실패 {}</span>'
              '<span><i style="background:var(--warn)"></i>건너뜀 {}</span></div>').format(p, f, s)
    return chart + legend


def _coverage_card(report: Report) -> str:
    items = []
    for cov in report.coverage:
        gate = coverage_gate(report, cov)
        for key in ("lines", "functions", "branches", "mcdc"):
            m = cov.totals.get(key)
            if m is None:
                continue
            g = gate[1] if gate and gate[0] == key else None
            items.append((f"{cov.name} {key}", m.percent, f"{m.percent:.1f}% ({m.covered}/{m.count})", g))
    return charts.hbars(items) + '<p class="note">점선 = 판정 기준</p>' if items else ""


def _cppcheck_card(report: Report) -> str:
    counts = {s: 0 for s in SEVERITIES}
    for v in report.cppcheck or []:
        counts[v.severity] = counts.get(v.severity, 0) + 1
    if not report.cppcheck:
        return '<p class="empty">위반 사항이 없습니다.</p>'
    return charts.vbars([(s, c, s if s in SEVERITIES else "information") for s, c in counts.items()])


CCN_BUCKETS = [("1-5", 1, 5), ("6-10", 6, 10), ("11-15", 11, 15), ("16-20", 16, 20), (">20", 21, 10 ** 9)]
LEN_BUCKETS = [("≤20", 0, 20), ("21-40", 21, 40), ("41-80", 41, 80), ("81-120", 81, 120), (">120", 121, 10 ** 9)]


def _histogram(values: List[int], buckets, limit: int) -> List[Tuple[str, float, str]]:
    out = []
    for label, lo, hi in buckets:
        n = sum(1 for v in values if lo <= v <= hi)
        out.append((label, n, "fail" if lo > limit else "pass"))
    return out


def _lizard_card(report: Report) -> str:
    funcs = report.lizard or []
    if not funcs:
        return ""
    ccn = charts.vbars(_histogram([f.ccn for f in funcs], CCN_BUCKETS, report.max_ccn), height=140)
    length = charts.vbars(_histogram([f.length for f in funcs], LEN_BUCKETS, report.max_length), height=140)
    return (f'<div class="note">순환복잡도(CCN) 분포 — 기준 {report.max_ccn} 이하</div>{ccn}'
            f'<div class="note">함수 라인수 분포 — 기준 {report.max_length} 이하</div>{length}')


def render_dashboard(report: Report, results: List[ToolResult]) -> str:
    overall = overall_status(results)
    verdict = {"pass": "모든 검증 기준을 충족했습니다.", "fail": "기준을 충족하지 못한 항목이 있습니다.",
               "na": "표시할 검증 결과가 없습니다."}[overall]
    cards = []
    for r in results:
        if r.status == "na":
            chart = '<p class="empty">이 도구의 결과 파일이 지정되지 않았습니다.</p>'
        elif r.key == "gtest":
            chart = _gtest_card(report, r)
        elif r.key == "coverage":
            chart = _coverage_card(report)
        elif r.key == "cppcheck":
            chart = _cppcheck_card(report)
        else:
            chart = _lizard_card(report) or '<p class="empty">함수 정보가 없습니다.</p>'
        cards.append(f'<article class="card"><h2>{h(r.title)}{badge(r.status)}</h2>'
                     f'<div class="headline">{h(r.headline)}</div><div class="sub">{h(r.sub)}</div>'
                     f'<div class="chartbox" style="flex-direction:column;align-items:stretch">{chart}</div>'
                     f'<a class="btn" href="{r.page}">상세 결과 보기</a></article>')
    rows = []
    for r in results:
        if not r.rows:
            rows.append(f'<tr><td>{h(r.title)}</td><td colspan="4" class="note">입력 없음</td>'
                        f'<td>{badge("na")}</td><td><a href="{r.page}">상세</a></td></tr>')
        for row in r.rows:
            rows.append(f'<tr><td>{h(r.title)}</td><td>{h(row.scope)}</td><td>{h(row.metric)}</td>'
                        f'<td class="num">{h(row.value)}</td><td class="num">{h(row.gate)}</td>'
                        f'<td>{row_badge(row.status)}</td>'
                        f'<td><a href="{r.page}">상세</a></td></tr>')
    summary = table([("도구", ""), ("세트", ""), ("지표", ""), ("결과", "num"), ("기준", "num"), ("판정", ""), ("", "")], rows)
    body = (page_header(report, report.build.title, "현재 빌드의 검증 결과 총괄")
            + f'<div class="banner {overall}">{badge(overall)}<span>{verdict}</span></div>'
            + f'<div class="grid">{"".join(cards)}</div>'
            + f'<section class="block"><h2>판정 요약</h2>{summary}</section>')
    return page(report, results, "index.html", "대시보드", body)


# --------------------------------------------------------------------------- Google Test
def render_gtest(report: Report, results: List[ToolResult]) -> str:
    parts = [page_header(report, "Google Test 상세 결과", "모듈(테스트 스위트) → 테스트 케이스")]
    if not report.tests:
        parts.append('<p class="empty">Google Test 결과가 지정되지 않았습니다.</p>')
    else:
        parts.append(toolbar("실패·건너뜀만"))
    for ts in report.tests:
        ok = ts.total > 0 and ts.failed == 0
        chart = charts.donut([("통과", ts.passed, "pass"), ("실패", ts.failed, "fail"), ("건너뜀", ts.skipped, "skip")],
                             f"{ts.pass_rate:.1f}%".replace(".0%", "%"), "성공률")
        stats = (f'<div class="chips"><span class="chip">전체 <b>{ts.total}</b></span>'
                 f'<span class="chip">통과 <b>{ts.passed}</b></span><span class="chip">실패 <b>{ts.failed}</b></span>'
                 f'<span class="chip">건너뜀 <b>{ts.skipped}</b></span>'
                 f'<span class="chip">실행 시간 <b>{ts.duration:.3f}s</b></span>'
                 f'{"<span class=chip>실행 시각 <b>" + h(ts.timestamp) + "</b></span>" if ts.timestamp else ""}</div>')
        parts.append(f'<h3 class="setname">{h(ts.name)} {badge("pass" if ok else "fail")}</h3>'
                     f'<div class="twocol"><div>{chart}</div><div>{stats}</div></div>')
        suites: "OrderedDict[str, list]" = OrderedDict()
        for c in ts.cases:
            suites.setdefault(c.suite, []).append(c)
        for suite, cases in suites.items():
            nfail = sum(c.status == "failed" for c in cases)
            nskip = sum(c.status == "skipped" for c in cases)
            rows = []
            for c in cases:
                cls = {"passed": "pass", "failed": "fail", "skipped": "na"}[c.status]
                label = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[c.status]
                msg = f'<pre class="msg">{h(c.message)}</pre>' if c.message else ""
                rows.append(f'<tr data-q="{h((ts.name + " " + suite + " " + c.name).lower())}" '
                            f'data-bad="{int(c.status != "passed")}"><td class="mono">{h(c.name)}{msg}</td>'
                            f'<td><span class="badge {cls}">{label}</span></td><td class="num">{c.time:.3f}s</td></tr>')
            pills = pill(f"{len(cases)}건") + (pill(f"실패 {nfail}", "bad") if nfail else pill("전체 통과", "ok")) \
                + (pill(f"건너뜀 {nskip}", "warn") if nskip else "")
            inner = table([("테스트 케이스", ""), ("결과", ""), ("시간", "num")], rows)
            parts.append(details("모듈", suite, pills, inner, f"{ts.name} {suite}", nfail + nskip > 0, "module",
                                 opened=nfail > 0))
    return page(report, results, "gtest.html", "Google Test", "".join(parts))


# --------------------------------------------------------------------------- 커버리지
def _metric_pill(key: str, m: Optional[CovMetric], gate: Optional[Tuple[str, float]]) -> str:
    if m is None:
        return ""
    if gate and gate[0] == key and m.percent < gate[1]:
        cls = "bad"
    else:
        cls = "ok" if m.percent >= 100.0 else "warn"
    return pill(f"{key[0].upper() if key != 'mcdc' else 'MC/DC'} {m.percent:.1f}%", cls)


def _sum_metrics(files: List[CovFile]) -> Dict[str, CovMetric]:
    out: Dict[str, CovMetric] = {}
    for f in files:
        for k, m in f.metrics.items():
            cur = out.get(k)
            out[k] = CovMetric((cur.covered if cur else 0) + m.covered, (cur.count if cur else 0) + m.count)
    return out


def _metric_pills(metrics: Dict[str, CovMetric], gate) -> str:
    return "".join(_metric_pill(k, metrics.get(k), gate) for k in ("lines", "functions", "regions", "branches", "mcdc"))


def _pct_or_dash(m: Optional[CovMetric]) -> str:
    return "-" if m is None else f"{m.percent:.1f}% ({m.covered}/{m.count})"


def _file_incomplete(f: CovFile, gate) -> bool:
    if gate and gate[0] in f.metrics:
        return f.metrics[gate[0]].percent < gate[1]
    return any(m.percent < 100.0 for m in f.metrics.values())


def _fn_badge(count: int, incomplete: bool) -> str:
    if count == 0:
        return badge("fail")
    return '<span class="badge warn">부분</span>' if incomplete else badge("pass")


def cov_status(results: List[ToolResult], name: str) -> str:
    """세트의 판정: 기준 행이 하나라도 fail 이면 fail, 기준 행이 있고 모두 pass 이면 pass, 없으면 na."""
    rows = [row for r in results if r.key == "coverage" for row in r.rows if row.scope == name and row.status != "na"]
    if not rows:
        return "na"
    return "fail" if any(row.status == "fail" for row in rows) else "pass"


def render_coverage(report: Report, results: List[ToolResult]) -> str:
    parts = [page_header(report, "LLVM 커버리지 상세 결과", "모듈 → 파일 → 함수")]
    if not report.coverage:
        parts.append('<p class="empty">커버리지 결과가 지정되지 않았습니다.</p>')
    else:
        parts.append(toolbar("기준 미달·미커버만"))
    for cov in report.coverage:
        gate = coverage_gate(report, cov)
        items = []
        for key in ("lines", "functions", "regions", "branches", "mcdc"):
            m = cov.totals.get(key)
            if m is not None:
                g = gate[1] if gate and gate[0] == key else None
                items.append((key, m.percent, f"{m.percent:.2f}% ({m.covered}/{m.count})", g))
        gate_txt = f"판정 기준: {gate[0]} ≥ {gate[1]:g}%" if gate else "판정 기준 없음(보고용)"
        parts.append(f'<h3 class="setname">{h(cov.name)}'
                     f'{badge(cov_status(results, cov.name))}'
                     f'</h3><p class="note">{h(gate_txt)}</p>{charts.hbars(items)}')
        if not cov.has_functions:
            parts.append('<p class="note">함수 단위 상세는 비-summary-only <code>llvm-cov export</code> JSON 이 있을 때 표시됩니다.</p>')
        tree = group_by_module(cov.files, lambda f: f.path)
        for module, files in tree.items():
            file_objs = [fs[0] for fs in files.values()]
            module_bad = any(_file_incomplete(f, gate) for f in file_objs)
            file_html = []
            for path, fs in files.items():
                f = fs[0]
                rows = []
                for fn in f.functions:
                    bad = fn.count == 0 or any(m is not None and m.percent < 100.0 for m in (fn.regions, fn.branches))
                    rows.append(f'<tr data-q="{h((cov.name + " " + module + " " + path + " " + fn.name).lower())}" '
                                f'data-bad="{int(bad)}"><td class="mono">{h(fn.name)}</td><td class="num">{fn.line or "-"}</td>'
                                f'<td class="num">{fn.count:,}</td><td class="num">{_pct_or_dash(fn.regions)}</td>'
                                f'<td class="num">{_pct_or_dash(fn.branches)}</td>'
                                f'<td>{_fn_badge(fn.count, bad)}</td></tr>')
                inner = table([("함수", ""), ("줄", "num"), ("실행 횟수", "num"), ("Region", "num"), ("Branch", "num"), ("", "")], rows) \
                    if rows else '<p class="note">함수 단위 데이터 없음</p>'
                file_html.append(details("파일", path, _metric_pills(f.metrics, gate), inner,
                                         f"{cov.name} {module} {path}", _file_incomplete(f, gate), "file"))
            parts.append(details("모듈", module, _metric_pills(_sum_metrics(file_objs), gate), "".join(file_html),
                                 f"{cov.name} {module}", module_bad, "module"))
    return page(report, results, "coverage.html", "LLVM 커버리지", "".join(parts))


# --------------------------------------------------------------------------- CppCheck
def render_cppcheck(report: Report, results: List[ToolResult]) -> str:
    parts = [page_header(report, "CppCheck 상세 결과", "모듈 → 파일 → 위반 (함수는 Lizard 결과가 있을 때 표시)")]
    violations = report.cppcheck
    if violations is None:
        parts.append('<p class="empty">CppCheck 결과가 지정되지 않았습니다.</p>')
        return page(report, results, "cppcheck.html", "CppCheck", "".join(parts))
    counts = {s: 0 for s in SEVERITIES}
    by_rule: Dict[str, int] = {}
    for v in violations:
        counts[v.severity] = counts.get(v.severity, 0) + 1
        by_rule[v.rule] = by_rule.get(v.rule, 0) + 1
    status = "pass" if not violations else "fail"
    parts.append(f'<div class="banner {status}">{badge(status)}<span>위반 {len(violations)}건 (기준: 0건, 억제 불가)</span></div>')
    if not violations:
        return page(report, results, "cppcheck.html", "CppCheck", "".join(parts))
    sev_items = [(s, c, s if s in SEVERITIES else "information") for s, c in counts.items() if c or s in SEVERITIES]
    parts.append(f'<div class="grid"><section class="card"><h2>심각도별</h2>{charts.vbars(sev_items)}</section>')
    rule_rows = [f'<tr><td class="mono">{h(r)}</td><td class="num">{n}</td></tr>'
                 for r, n in sorted(by_rule.items(), key=lambda kv: (-kv[1], kv[0]))]
    parts.append(f'<section class="card"><h2>규칙별</h2>{table([("규칙 ID", ""), ("건수", "num")], rule_rows)}</section></div>')
    parts.append(toolbar("위반만"))
    tree = group_by_module(violations, lambda v: v.file)
    for module, files in tree.items():
        mod_total = sum(len(vs) for vs in files.values())
        file_html = []
        for path, vs in files.items():
            rows = []
            for v in sorted(vs, key=lambda x: (x.line, x.rule)):
                rows.append(f'<tr data-q="{h((module + " " + path + " " + v.function + " " + v.rule + " " + v.message).lower())}" '
                            f'data-bad="1"><td class="num">{v.line}</td><td class="mono">{h(v.function) or "-"}</td>'
                            f'<td><span class="pill {"bad" if v.severity == "error" else "warn"}">{h(v.severity)}</span></td>'
                            f'<td class="mono">{h(v.rule)}</td><td>{h(v.message)}</td></tr>')
            inner = table([("줄", "num"), ("함수", ""), ("심각도", ""), ("규칙", ""), ("메시지", "")], rows)
            file_html.append(details("파일", path, pill(f"{len(vs)}건", "bad"), inner, f"{module} {path}", True, "file"))
        parts.append(details("모듈", module, pill(f"{mod_total}건", "bad"), "".join(file_html), module, True, "module",
                             opened=True))
    return page(report, results, "cppcheck.html", "CppCheck", "".join(parts))


# --------------------------------------------------------------------------- Lizard
def render_lizard(report: Report, results: List[ToolResult]) -> str:
    parts = [page_header(report, "Lizard 상세 결과", f"순환복잡도 {report.max_ccn} 초과, 함수 라인수 {report.max_length} 초과 함수")]
    funcs = report.lizard
    if funcs is None:
        parts.append('<p class="empty">Lizard 결과가 지정되지 않았습니다.</p>')
        return page(report, results, "lizard.html", "Lizard", "".join(parts))
    bad_funcs = report.lizard_violations()
    status = "pass" if not bad_funcs else "fail"
    parts.append(f'<div class="banner {status}">{badge(status)}<span>전체 {len(funcs)}개 함수 중 기준 초과 {len(bad_funcs)}개</span></div>')
    if any(f.length_estimated for f in funcs):
        parts.append('<p class="note">XML 입력에는 함수 라인수(length)가 없어 NCSS 로 대신했습니다. 정확한 판정은 <code>lizard --csv</code> 결과를 사용하세요.</p>')
    ccn = charts.vbars(_histogram([f.ccn for f in funcs], CCN_BUCKETS, report.max_ccn), height=150)
    length = charts.vbars(_histogram([f.length for f in funcs], LEN_BUCKETS, report.max_length), height=150)
    parts.append(f'<div class="grid"><section class="card"><h2>순환복잡도(CCN) 분포</h2>{ccn}</section>'
                 f'<section class="card"><h2>함수 라인수 분포</h2>{length}</section></div>')
    parts.append(toolbar("기준 초과 함수만", bad_checked=bool(bad_funcs)))
    tree = group_by_module(funcs, lambda f: f.file)
    for module, files in tree.items():
        mod_funcs = [f for fs in files.values() for f in fs]
        mod_bad = sum(1 for f in mod_funcs if report.lizard_reasons(f))
        file_html = []
        for path, fs in files.items():
            rows = []
            for f in fs:
                reasons = report.lizard_reasons(f)
                ccn_cls = "bad" if f.ccn > report.max_ccn else ""
                len_cls = "bad" if f.length > report.max_length else ""
                rows.append(f'<tr data-q="{h((module + " " + path + " " + f.name).lower())}" data-bad="{int(bool(reasons))}">'
                            f'<td class="mono">{h(f.name)}</td><td class="num">{f.start}-{f.end}</td>'
                            f'<td class="num"><span class="pill {ccn_cls}">{f.ccn}</span></td>'
                            f'<td class="num"><span class="pill {len_cls}">{f.length}</span></td>'
                            f'<td class="num">{f.nloc}</td><td class="num">{f.params}</td>'
                            f'<td>{badge("fail") if reasons else badge("pass")} {h(", ".join(reasons))}</td></tr>')
            nbad = sum(1 for f in fs if report.lizard_reasons(f))
            inner = table([("함수", ""), ("줄", "num"), ("CCN", "num"), ("라인수", "num"), ("NLOC", "num"), ("인자", "num"), ("판정", "")], rows)
            file_html.append(details("파일", path, pill(f"초과 {nbad}", "bad") if nbad else pill(f"{len(fs)}개 함수", "ok"),
                                     inner, f"{module} {path}", nbad > 0, "file", opened=nbad > 0))
        parts.append(details("모듈", module, pill(f"초과 {mod_bad}", "bad") if mod_bad else pill(f"{len(mod_funcs)}개 함수", "ok"),
                             "".join(file_html), module, mod_bad > 0, "module", opened=mod_bad > 0))
    return page(report, results, "lizard.html", "Lizard", "".join(parts))


# --------------------------------------------------------------------------- 출력
def write_report(report: Report, out_dir: str) -> List[Path]:
    report.resolve_functions()
    results = evaluate(report)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pages = {"index.html": render_dashboard(report, results), "gtest.html": render_gtest(report, results),
             "coverage.html": render_coverage(report, results), "cppcheck.html": render_cppcheck(report, results),
             "lizard.html": render_lizard(report, results)}
    written = []
    for name, html in pages.items():
        path = out / name
        path.write_text(html, encoding="utf-8")
        written.append(path)
    return written
