# -*- coding: utf-8 -*-
"""Unit tests for the text extractors in audit_pdf.py."""

from audit_pdf import cn_to_int, extract_clauses, extract_numbers, extract_refs


def test_cn_to_int():
    assert cn_to_int("三") == 3
    assert cn_to_int("十") == 10
    assert cn_to_int("十二") == 12
    assert cn_to_int("二十") == 20
    assert cn_to_int("二十五") == 25
    assert cn_to_int("7") == 7
    assert cn_to_int("甲") is None


def test_clauses_headings_and_multilevel():
    text = "2.1 General\n  2.1.1 Scope\n(3.2) Notes\ninline ref to 4.2.7 here"
    assert extract_clauses(text) == ["2.1", "2.1.1", "3.2", "4.2.7"]


def test_clauses_ignore_plain_decimals():
    # inline decimals and decimals with leading-zero fractions are not clauses
    text = "Thickness is 4.5 mm and price 200.00 KWD\n200.00\n0.05 tolerance"
    assert extract_clauses(text) == []


def test_refs_cross_language():
    en = "Section 1, Appendix-3, Annex B, Table 2 and Figure 4"
    zh = "第一部分、附录-3、附件B、表2 及 图4"
    assert extract_refs(en) == {"sec:1", "app:3", "app:B", "tab:2", "fig:4"}
    assert extract_refs(en) == extract_refs(zh)


def test_refs_ignore_chinese_words_after_biao():
    # '表示' / '表格' must not be parsed as table references
    assert extract_refs("这表示表格内容") == set()


def test_numbers_normalisation():
    assert "150000" in extract_numbers("capacity 150,000 tonnes")
    assert extract_numbers("150,000") == extract_numbers("150000")
    assert extract_numbers("200.00 ppm") == {"200"}
    assert extract_numbers("4.5毫米") == {"4.5"}


def test_numbers_skip_single_digits_and_clause_tokens():
    assert extract_numbers("Step 3 of 2.1.1") == set()
    assert extract_numbers("ISO 9001 since 2009") == {"9001", "2009"}
