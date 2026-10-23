# -*- coding: utf-8 -*-
"""Integration tests: each deliberately defective translation must be caught by audit_pdf."""

import json

from audit_pdf import audit_document, main
from conftest import LETTER, TGT_PAGES


def _messages(report):
    msgs = [i["message"] for i in report["document_issues"]]
    for p in report["pages"]:
        msgs += [i["message"] for i in p["issues"]]
    return msgs


def _audit(src, tgt, **kw):
    return audit_document(src, tgt, quiet=True, **kw)


def test_faithful_translation_passes(src_pdf, tgt_factory):
    passed, report = _audit(src_pdf, tgt_factory())
    assert passed, _messages(report)
    assert report["summary"]["critical_errors"] == 0


def test_missing_clause_is_warning_and_fails_in_strict(src_pdf, tgt_factory):
    pages = list(TGT_PAGES)
    pages[0] = pages[0].replace("2.1.1 ISO 9001 证书\n", "")
    tgt = tgt_factory(pages)

    passed, report = _audit(src_pdf, tgt)
    assert passed  # warnings only
    assert any("2.1.1" in m and "clause" in m for m in _messages(report))

    passed_strict, _ = _audit(src_pdf, tgt, strict=True)
    assert not passed_strict


def test_changed_number_detected(src_pdf, tgt_factory):
    pages = list(TGT_PAGES)
    pages[0] = pages[0].replace("150,000", "100,000")
    passed, report = _audit(src_pdf, tgt_factory(pages), strict=True)
    assert not passed
    assert any("150000" in m for m in _messages(report))


def test_missing_appendix_ref_detected(src_pdf, tgt_factory):
    pages = list(TGT_PAGES)
    pages[0] = pages[0].replace("附录-3及", "")
    _, report = _audit(src_pdf, tgt_factory(pages))
    assert any("app:3" in m for m in _messages(report))


def test_extra_page_is_critical(src_pdf, tgt_factory):
    passed, report = _audit(src_pdf, tgt_factory(list(TGT_PAGES) + ["多出来的一页内容，用于测试额外页面检测。"]))
    assert not passed
    assert any("Page count mismatch" in m for m in _messages(report))
    assert any("Extra page" in m for m in _messages(report))


def test_placeholder_is_critical(src_pdf, tgt_factory):
    pages = list(TGT_PAGES)
    pages[1] = pages[1] + "\n其余条款因篇幅省略。"
    passed, report = _audit(src_pdf, tgt_factory(pages))
    assert not passed
    assert any("因篇幅省略" in m for m in _messages(report))


def test_placeholder_present_in_source_is_not_flagged(tmp_path):
    from conftest import make_pdf
    src = make_pdf(str(tmp_path / "s.pdf"), ["Delivery date: TBD\nSection 1 general terms of contract."], cjk=False)
    tgt = make_pdf(str(tmp_path / "t.pdf"), ["交货日期：TBD\n第1部分 合同一般条款内容说明。"])
    passed, report = _audit(src, tgt)
    assert passed, _messages(report)


def test_page_size_mismatch_is_critical(src_pdf, tgt_factory):
    passed, report = _audit(src_pdf, tgt_factory(rect=LETTER))
    assert not passed
    assert any("Page size mismatch" in m for m in _messages(report))


def test_full_page_raster_is_critical(src_pdf, tgt_factory):
    passed, report = _audit(src_pdf, tgt_factory(full_page_image_on=0))
    assert not passed
    assert any("full-page raster" in m for m in _messages(report))


def test_ignore_regex_suppresses(src_pdf, tgt_factory):
    pages = list(TGT_PAGES)
    pages[0] = pages[0].replace("2009", "二〇〇九")
    _, report = _audit(src_pdf, tgt_factory(pages), ignore=r"^(19|20)\d\d$")
    assert not any("2009" in m for m in _messages(report))


def test_compare_png_written(src_pdf, tgt_factory, tmp_path):
    out = tmp_path / "cmp"
    _, report = _audit(src_pdf, tgt_factory(), compare_png=str(out), compare_pages="1")
    assert len(report["comparison_pngs"]) == 1
    assert (out / "compare_page_001.png").stat().st_size > 0


def test_cli_json_out_alias_and_exit_codes(src_pdf, tgt_factory, tmp_path):
    good = tgt_factory()
    js = tmp_path / "r" / "report.json"
    assert main(["--src", src_pdf, "--tgt", good, "--json-out", str(js)]) == 0
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data["summary"]["passed"] is True

    bad = tgt_factory(rect=LETTER, name="bad.pdf")
    assert main(["--src", src_pdf, "--tgt", bad, "--json", str(js)]) == 1
