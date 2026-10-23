# -*- coding: utf-8 -*-
"""Tests for render_pdf.py overflow probe (skipped when no Playwright browser is available)."""

import pytest

pytest.importorskip("playwright")

from render_pdf import render_html_to_pdf  # noqa: E402

PAGE_CSS = """
<style>
@page { size: A4; margin: 0; }
* { margin: 0; padding: 0; box-sizing: border-box; }
.page { width: 210mm; height: 297mm; overflow: hidden; display: flex; flex-direction: column; padding: 20mm; }
.content-area { flex: 1; overflow: hidden; }
</style>
"""


def _html(tmp_path, body, name="doc.html"):
    p = tmp_path / name
    p.write_text(f"<!DOCTYPE html><html><head><meta charset='utf-8'>{PAGE_CSS}</head><body>{body}</body></html>",
                 encoding="utf-8")
    return str(p)


def _render(*args, **kw):
    try:
        return render_html_to_pdf(*args, **kw)
    except RuntimeError as e:  # no browser installed
        pytest.skip(str(e))


def test_clean_pages_pass(tmp_path):
    html = _html(tmp_path, "<div class='page'><div class='content-area'>ok</div></div>" * 2)
    out = tmp_path / "ok.pdf"
    assert _render(html, str(out), strict_overflow=True) is True
    assert out.exists()


def test_nested_content_area_overflow_detected(tmp_path):
    # Regression: content clipped by an inner overflow:hidden wrapper used to slip through
    html = _html(tmp_path, "<div class='page'><div class='content-area'><div style='height:2000mm'>x</div></div></div>")
    out = tmp_path / "bad.pdf"
    assert _render(html, str(out), strict_overflow=True) is False
    assert not out.exists()


def test_page_count_mismatch_detected(tmp_path):
    # .page taller than @page -> each container spills onto 2 PDF pages
    body = "<div class='page' style='height:320mm'><div class='content-area'>x</div></div>"
    out = tmp_path / "spill.pdf"
    assert _render(_html(tmp_path, body), str(out)) is False
