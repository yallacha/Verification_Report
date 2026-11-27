# Verification_Report

테스트, 정적 분석 등의 결과를 한 번에 보여준다.

Google Test, LLVM 커버리지, CppCheck, Lizard 결과 파일을 읽어 **HTML 대시보드**와 도구별 **상세 결과 페이지**를 만든다.
Python 표준 라이브러리만 쓰며(외부 패키지·CDN 없음) 생성된 HTML은 오프라인에서 그대로 열린다.

## 빠른 시작

```
python -m verification_report ^
  --gtest unit=build/reports/unit/test-results.xml ^
  --gtest integration=build/reports/integration/test-results.xml ^
  --coverage unit=build/reports/unit/export.json ^
  --coverage integration=build/reports/integration/export.json ^
  --cppcheck build/reports/cppcheck/cppcheck.xml ^
  --lizard build/reports/lizard/lizard.csv ^
  --build-id 128 --branch develop --commit a10bccd --out report
```

`report/index.html`을 열면 된다. 샘플 입력은 `samples/`에 있다.

```
python -m verification_report --gtest unit=samples/unit-results.xml --coverage unit=samples/unit-coverage.json ^
  --cppcheck samples/cppcheck.xml --lizard samples/lizard.csv --out report
```

## 화면 구성

| 페이지 | 내용 |
|---|---|
| `index.html` 대시보드 | 빌드 일시·번호·브랜치·커밋, 전체 판정, 도구별 카드(차트 + **상세 결과 보기** 버튼), 판정 요약 표 |
| `gtest.html` | 세트별 성공률 도넛, 모듈(테스트 스위트) → 테스트 케이스, 실패 메시지 |
| `coverage.html` | 세트별 lines/functions/regions/branches/MC-DC 막대(기준선 표시), 모듈 → 파일 → 함수 |
| `cppcheck.html` | 심각도·규칙별 집계, 모듈 → 파일 → 위반(줄, 함수, 규칙, 메시지) |
| `lizard.html` | CCN·함수 라인수 분포, 모듈 → 파일 → 함수 (기본은 기준 초과 함수만) |

상세 페이지에는 검색, "문제 항목만" 필터, 모두 펼치기/접기가 있다. 다크 모드를 지원한다.

## 입력 형식과 생성 방법

| 도구 | 옵션 | 형식 | 생성 방법 |
|---|---|---|---|
| Google Test | `--gtest [이름=]경로` (반복 가능) | XML 또는 JSON | `--gtest_output=xml:파일` (`ci/quality.sh`가 `test-results.xml` 생성) |
| LLVM 커버리지 | `--coverage [이름=]경로` (반복 가능) | `llvm-cov export` JSON | 아래 참고 |
| CppCheck | `--cppcheck 경로` | XML v2 | `cppcheck --xml --xml-version=2 ...` |
| Lizard | `--lizard 경로` | **CSV 권장**, XML 가능 | `lizard src -l c --csv > lizard.csv` |

- **LLVM 커버리지**: `ci/quality.sh`가 만드는 `summary.json`(`-summary-only`)은 **파일 단위**까지 표시된다. **함수 단위**(실행 횟수, region, branch)까지 보려면 `-summary-only` 없이 내보낸 JSON이 필요하다.
  ```
  llvm-cov export out/test_bin -instr-profile=out/test.profdata -ignore-filename-regex=... > out/export.json
  ```
  함수 단위 MC/DC는 llvm-cov JSON에서 함수별로 안정적으로 얻을 수 없어 파일·모듈·총괄 단위로만 표시한다.
- **Lizard**: XML에는 함수 라인수(length)가 없어 NCSS로 대신하고 화면에 안내를 표시한다. 정확한 판정은 CSV를 쓴다.
- 입력을 주지 않은 도구는 `N/A`(입력 없음)로 표시되고 전체 판정에서 제외된다.

## 판정 기준

`Claude_Clang`의 `CLAUDE.md` 2장 기준과 같다. 모두 옵션으로 바꿀 수 있다.

| 항목 | 기본 기준 | 옵션 |
|---|---|---|
| Google Test | 세트마다 실패 0건, 테스트 1건 이상 | - |
| 커버리지 | `unit`: MC/DC 100%, `integration`: 함수 100%. 그 밖의 세트는 보고용 | `--gate 세트:지표:최소%` |
| CppCheck | 위반 0건 | - |
| Lizard | CCN 10 이하, 함수 라인수 80 이하 | `--max-ccn`, `--max-length` |

`--fail-on-violation`을 주면 기준 미달일 때 종료 코드 1을 반환한다(CI 용).

## 모듈·파일·함수 구분

- **파일**: 경로를 저장소 기준(`src/...`)으로 정규화한다. `--source-root /work/`로 접두어를 제거하고, `--root-dir`로 시작 디렉터리(기본 `src include tests`)를 바꾼다.
- **모듈**: `src/` 아래 첫 하위 디렉터리, 파일이 바로 `src/`에 있으면 파일 이름(확장자 제외)이다. `src/foo.c`와 `include/foo.h`는 모듈 `foo`로 묶인다.
- **함수**: 커버리지(함수 단위 JSON)와 Lizard는 함수 단위, CppCheck는 위반의 `파일:줄`을 Lizard 함수 범위와 대조해 함수 이름을 채운다(Lizard 입력이 있을 때).
- Google Test는 테스트 스위트를 모듈로, 테스트 케이스를 함수 단위로 본다.

## 테스트

```
python -m unittest discover -s tests -v
```

## 구성

```
verification_report/
  cli.py        명령행, 입력 읽기
  parsers/      gtest, llvm_cov, cppcheck, lizard 파서
  summary.py    판정 기준 적용, 도구별 총괄
  render.py     대시보드/상세 페이지 HTML
  charts.py     인라인 SVG 차트(도넛, 가로/세로 막대)
  assets.py     CSS, JS
samples/        실제 도구 출력 형식의 샘플
tests/          unittest
```
