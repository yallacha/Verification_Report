"""파서, 판정, 렌더링 테스트. 실행: python -m unittest discover -s tests -v"""
import tempfile
import unittest
from pathlib import Path

from verification_report.cli import main
from verification_report.models import BuildInfo
from verification_report.parsers import parse_cppcheck, parse_gtest, parse_lizard, parse_llvm_cov
from verification_report.summary import Report, evaluate, overall_status
from verification_report.util import module_of, norm_path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class UtilTest(unittest.TestCase):
    def test_norm_path(self):
        self.assertEqual(norm_path("/work/src/a.c"), "src/a.c")
        self.assertEqual(norm_path("./src/a.c"), "src/a.c")
        self.assertEqual(norm_path("C:\\w\\src\\sub\\a.c"), "src/sub/a.c")
        self.assertEqual(norm_path("/opt/build/src/a.c", strip=["/opt/build/"]), "src/a.c")

    def test_module_of(self):
        self.assertEqual(module_of("src/foo.c"), "foo")
        self.assertEqual(module_of("include/foo.h"), "foo")
        self.assertEqual(module_of("src/log/log.c"), "log")


class ParserTest(unittest.TestCase):
    def test_gtest(self):
        t = parse_gtest(str(SAMPLES / "unit-results.xml"), "unit")
        self.assertEqual((t.total, t.passed, t.failed, t.skipped), (11, 9, 1, 1))
        failed = [c for c in t.cases if c.status == "failed"][0]
        self.assertEqual(failed.name, "FireReleasesUnlessRisk")
        self.assertIn("Expected equality", failed.message)

    def test_gtest_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.json"
            p.write_text('{"timestamp":"t","testsuites":[{"name":"S","testsuite":['
                         '{"name":"a","status":"RUN","result":"COMPLETED","time":"0.002s"},'
                         '{"name":"b","status":"RUN","result":"COMPLETED","time":"0s","failures":[{"failure":"boom"}]}]}]}',
                         encoding="utf-8")
            t = parse_gtest(str(p))
            self.assertEqual((t.passed, t.failed), (1, 1))

    def test_llvm_cov_function_level(self):
        c = parse_llvm_cov(str(SAMPLES / "unit-coverage.json"), "unit")
        self.assertTrue(c.has_functions)
        self.assertEqual(c.totals["mcdc"].count, 39)
        over = [f for f in c.files if f.path == "src/override.c"][0]
        clear = [f for f in over.functions if f.name == "override_clear"][0]
        self.assertEqual(clear.count, 0)

    def test_llvm_cov_summary_only(self):
        c = parse_llvm_cov(str(SAMPLES / "integration-coverage.json"), "integration")
        self.assertFalse(c.has_functions)
        self.assertEqual(len(c.files), 4)

    def test_cppcheck(self):
        v = parse_cppcheck(str(SAMPLES / "cppcheck.xml"))
        self.assertEqual(len(v), 5)
        self.assertEqual(sorted({x.file for x in v})[0], "src/arbitration.c")

    def test_lizard_csv(self):
        f = parse_lizard(str(SAMPLES / "lizard.csv"))
        self.assertEqual(len(f), 9)
        sel = [x for x in f if x.name == "select_priority"][0]
        self.assertEqual((sel.ccn, sel.length, sel.file), (14, 96, "src/arbitration.c"))

    def test_lizard_xml(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "l.xml"
            p.write_text('<?xml version="1.0"?><cppncss><measure type="Function"><labels><label>Nr.</label>'
                         '<label>NCSS</label><label>CCN</label></labels><item name="f(...) at ./src/a.c:7">'
                         '<value>1</value><value>12</value><value>3</value></item></measure></cppncss>', encoding="utf-8")
            f = parse_lizard(str(p))
            self.assertEqual((f[0].name, f[0].file, f[0].start, f[0].ccn, f[0].length_estimated),
                             ("f(...)", "src/a.c", 7, 3, True))


class SummaryTest(unittest.TestCase):
    def _report(self):
        r = Report(build=BuildInfo())
        r.tests = [parse_gtest(str(SAMPLES / "unit-results.xml"), "unit")]
        r.coverage = [parse_llvm_cov(str(SAMPLES / "unit-coverage.json"), "unit")]
        r.cppcheck = parse_cppcheck(str(SAMPLES / "cppcheck.xml"))
        r.lizard = parse_lizard(str(SAMPLES / "lizard.csv"))
        return r

    def test_gates(self):
        report = self._report()
        results = {x.key: x for x in evaluate(report)}
        self.assertEqual(results["gtest"].status, "fail")
        self.assertEqual(results["coverage"].status, "fail")  # unit MC/DC 89.7% < 100%
        self.assertEqual(results["cppcheck"].status, "fail")
        self.assertEqual(results["lizard"].status, "fail")
        self.assertEqual(len(report.lizard_violations()), 3)

    def test_all_pass_and_na(self):
        r = Report(build=BuildInfo())
        self.assertEqual(overall_status(evaluate(r)), "na")
        r.cppcheck, r.lizard = [], []
        self.assertEqual(overall_status(evaluate(r)), "pass")

    def test_function_resolution(self):
        r = self._report()
        r.resolve_functions()
        by_rule = {v.rule: v.function for v in r.cppcheck}
        self.assertEqual(by_rule["uninitvar"], "select_priority")
        self.assertEqual(by_rule["unusedStructMember"], "")


class CliTest(unittest.TestCase):
    def test_generates_pages(self):
        with tempfile.TemporaryDirectory() as d:
            rc = main(["--gtest", f"unit={SAMPLES / 'unit-results.xml'}",
                       "--coverage", f"unit={SAMPLES / 'unit-coverage.json'}",
                       "--cppcheck", str(SAMPLES / "cppcheck.xml"), "--lizard", str(SAMPLES / "lizard.csv"),
                       "--out", d, "--build-id", "7", "--build-time", "2026-11-27 10:00:00", "--fail-on-violation"])
            self.assertEqual(rc, 1)
            index = (Path(d) / "index.html").read_text(encoding="utf-8")
            for name in ("gtest", "coverage", "cppcheck", "lizard"):
                self.assertTrue((Path(d) / f"{name}.html").exists())
                self.assertIn(f'href="{name}.html"', index)
            self.assertIn("2026-11-27 10:00:00", index)
            self.assertIn("상세 결과 보기", index)
            self.assertIn("<svg", index)
            self.assertIn("<table", index)

    def test_html_is_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            x = Path(d) / "c.xml"
            x.write_text('<results version="2"><errors><error id="a" severity="error" '
                         'msg="&lt;script&gt;alert(1)&lt;/script&gt;"><location file="src/a.c" line="1"/></error>'
                         '</errors></results>', encoding="utf-8")
            main(["--cppcheck", str(x), "--out", d])
            html = (Path(d) / "cppcheck.html").read_text(encoding="utf-8")
            self.assertNotIn("<script>alert(1)", html)
            self.assertIn("&lt;script&gt;alert(1)", html)

    def test_missing_file_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main(["--cppcheck", str(Path(d) / "nope.xml"), "--out", d]), 2)

    def test_no_inputs_renders_empty_report(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main(["--out", d]), 0)
            self.assertIn("입력 없음", (Path(d) / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
