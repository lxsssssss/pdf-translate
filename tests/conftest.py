# -*- coding: utf-8 -*-
"""Shared fixtures: build small source / translated PDFs on the fly (no binary fixtures in git)."""

import os
import sys

import fitz
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

A4 = fitz.paper_rect("a4")
LETTER = fitz.paper_rect("letter")

SRC_PAGES = [
    "Section 2: Qualification Requirements\n"
    "2.1 Manufacturer Qualification\n"
    "2.1.1 ISO 9001 certificate\n"
    "2.1.2 Annual capacity not less than 150,000 tonnes\n"
    "Refer to Appendix-3 and Table 2 for details.\n"
    "Minimum experience: 15 years since 2009.",
    "2.2 Submission\n"
    "Bids shall be valid for 120 days.\n"
    "See Figure 1. Lining thickness 4.5 mm.",
]

TGT_PAGES = [
    "第2部分：资质要求\n"
    "2.1 制造商资质\n"
    "2.1.1 ISO 9001 证书\n"
    "2.1.2 年产能不低于 150,000 吨\n"
    "详见附录-3及表2。\n"
    "最低经验：自2009年起15年。",
    "2.2 递交\n"
    "投标有效期为120天。\n"
    "见图1。内衬厚度4.5毫米。",
]


def make_pdf(path, pages, rect=A4, full_page_image_on=None, cjk=True):
    doc = fitz.open()
    for i, text in enumerate(pages):
        page = doc.new_page(width=rect.width, height=rect.height)
        page.insert_text((72, 90), text, fontsize=11, fontname="china-s" if cjk else "helv")
        if full_page_image_on is not None and i == full_page_image_on:
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40), False)
            pix.clear_with(200)
            page.insert_image(page.rect, pixmap=pix)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def src_pdf(tmp_path):
    return make_pdf(str(tmp_path / "src.pdf"), SRC_PAGES, cjk=False)


@pytest.fixture
def tgt_factory(tmp_path):
    def _make(pages=None, name="tgt.pdf", **kw):
        return make_pdf(str(tmp_path / name), pages if pages is not None else list(TGT_PAGES), **kw)
    return _make
