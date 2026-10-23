# -*- coding: utf-8 -*-
"""
Universal Automated PDF Translation Audit and Diff Engine
Skill: pdf-translate
Script: audit_pdf.py

Performs a page-by-page 1:1 structural, numerical and textual audit between
the source PDF and the translated vector PDF.

Checks (severity in brackets; --strict promotes every WARNING to a failure):
  1. Page count                                   [CRITICAL]
  2. Page size per page (default tolerance 2pt)   [CRITICAL]
  3. Full-page raster scans in target             [CRITICAL]
  4. U+FFFD replacement chars (broken glyphs)     [CRITICAL]
  5. Placeholder / fabrication phrases that appear in target but not in source  [CRITICAL]
  6. Missing clause numbers (2.1, 2.1.1, ...)     [WARNING]
  7. Missing structural refs (Section/Appendix/Table/Figure <-> 第N部分/附录/表/图) [WARNING]
  8. Missing numeric values (amounts, years, thresholds)  [WARNING]
  9. Image count / size mismatch per page         [WARNING]
 10. Blank target page where source has text      [WARNING]
 11. Non-embedded fonts in target                 [WARNING]

Optional: --compare-png DIR renders side-by-side source|target PNGs for visual review.
"""

import sys
import os
import re
import json
import argparse
from decimal import Decimal, InvalidOperation

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF (fitz) is required. Install via `pip install pymupdf`")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KEYWORDS_FILE = os.path.join(SCRIPT_DIR, "keywords.json")

CRITICAL = "CRITICAL"
WARNING = "WARNING"

# --------------------------------------------------------------------------- #
# Keyword loading
# --------------------------------------------------------------------------- #

_FALLBACK_KEYWORDS = ["暂缺", "待补充", "此处略", "因篇幅省略", "详见英文原版", "TBD", "TODO"]


def load_keywords(path: str = None):
    path = path or DEFAULT_KEYWORDS_FILE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return list(_FALLBACK_KEYWORDS)
    words = []
    for key, val in data.items():
        if not key.startswith("_") and isinstance(val, list):
            words.extend(str(v) for v in val if str(v).strip())
    return words or list(_FALLBACK_KEYWORDS)


# --------------------------------------------------------------------------- #
# Clause numbers (2.1 / 2.1.1 / (3.2) ...)
# --------------------------------------------------------------------------- #

# first component 1-3 digits, following components 1-2 digits without leading zero
_CLAUSE_CORE = r"\d{1,3}(?:\.[1-9]\d?)+"
# multi-level (>= 3 components) anywhere in text
_CLAUSE_MULTI_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.[1-9]\d?){2,})(?![\d]|\.\d)")
# two-level only when it starts a line (heading / list item / table first cell)
_CLAUSE_HEAD_RE = re.compile(r"^\s*[\(（]?(" + _CLAUSE_CORE + r")[\)）]?\.?(?=\s|[-–—:：]|$)", re.MULTILINE)


def extract_clauses(text: str):
    """Return ordered unique clause numbers such as '2.1', '2.1.1'."""
    found = []
    seen = set()
    for regex in (_CLAUSE_HEAD_RE, _CLAUSE_MULTI_RE):
        for m in regex.finditer(text):
            c = m.group(1).rstrip(".")
            if c not in seen:
                seen.add(c)
                found.append(c)
    return found


# --------------------------------------------------------------------------- #
# Structural references, normalised across languages
# --------------------------------------------------------------------------- #

_CN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s: str):
    """Convert simple Chinese numerals (一 .. 九十九) to int; return None if not parseable."""
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if "十" in s:
        left, _, right = s.partition("十")
        tens = _CN_DIGITS.get(left, None) if left else 1
        ones = _CN_DIGITS.get(right, None) if right else 0
        if tens is None or ones is None:
            return None
        return tens * 10 + ones
    if all(ch in _CN_DIGITS for ch in s):
        return int("".join(str(_CN_DIGITS[ch]) for ch in s))
    return None


def _norm_ref_id(raw: str):
    raw = raw.strip().strip("()（）")
    n = cn_to_int(raw)
    if n is not None:
        return str(n)
    if len(raw) == 1 and raw.isalpha():
        return raw.upper()
    return None


_SEP = r"\s*[-–—.:：]?\s*"
_ID = r"[\(（]?\s*(\d{1,3}|[A-Za-z](?![A-Za-z])|[一二三四五六七八九十]{1,3})\s*[\)）]?"
_REF_PATTERNS = [
    ("sec", re.compile(r"(?<![A-Za-z])(?:section|chapter|part)" + _SEP + _ID, re.IGNORECASE)),
    ("sec", re.compile(r"第\s*[\(（]?\s*(\d{1,3}|[一二三四五六七八九十]{1,3})\s*[\)）]?\s*(?:部分|章|节)")),
    ("app", re.compile(r"(?<![A-Za-z])(?:appendix|annex(?:ure)?)" + _SEP + _ID, re.IGNORECASE)),
    ("app", re.compile(r"(?:附录|附件|附表)" + _SEP + _ID)),
    ("tab", re.compile(r"(?<![A-Za-z])(?:table|tab\.)" + _SEP + r"(\d{1,3}|[A-Z](?![A-Za-z]))", re.IGNORECASE)),
    ("tab", re.compile(r"表" + _SEP + r"(\d{1,3}|[A-Z](?![A-Za-z]))")),
    ("fig", re.compile(r"(?<![A-Za-z])(?:figure|fig\.)" + _SEP + r"(\d{1,3})", re.IGNORECASE)),
    ("fig", re.compile(r"图" + _SEP + r"(\d{1,3})")),
]


def extract_refs(text: str):
    """Return set of canonical structural references, e.g. {'sec:1', 'app:3', 'tab:2'}."""
    refs = set()
    for kind, regex in _REF_PATTERNS:
        for m in regex.finditer(text):
            rid = _norm_ref_id(m.group(1))
            if rid is not None:
                refs.add(f"{kind}:{rid}")
    return refs


# --------------------------------------------------------------------------- #
# Numeric values
# --------------------------------------------------------------------------- #

_CLAUSE_TOKEN_RE = re.compile(r"(?<![\d.])\d+(?:\.\d+){2,}(?![\d])")
_NUM_RE = re.compile(
    r"(?<![A-Za-z0-9_.,])"
    r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?![0-9]|[.,]\d)"
)


def _normalise_number(tok: str):
    tok = tok.replace(",", "")
    try:
        d = Decimal(tok)
    except InvalidOperation:
        return None
    s = format(d.normalize(), "f")
    return s


def extract_numbers(text: str, min_digits: int = 2):
    """Return set of normalised numbers with at least `min_digits` digits (or any decimal)."""
    text = _CLAUSE_HEAD_RE.sub(" ", _CLAUSE_TOKEN_RE.sub(" ", text))
    nums = set()
    for m in _NUM_RE.finditer(text):
        tok = m.group(1)
        digits = sum(ch.isdigit() for ch in tok)
        if digits < min_digits and "." not in tok:
            continue
        n = _normalise_number(tok)
        if n is not None:
            nums.add(n)
    return nums


# --------------------------------------------------------------------------- #
# Page helpers
# --------------------------------------------------------------------------- #

def _visible_text(page) -> str:
    """Extract page text excluding blocks completely covered by opaque white-filled rectangles."""
    white_rects = [
        d["rect"] for d in page.get_drawings()
        if d.get("fill") == (1.0, 1.0, 1.0) and d.get("fill_opacity", 1.0) >= 0.95
        and d["rect"].width < page.rect.width * 0.95
    ]
    if not white_rects:
        return page.get_text().strip()
    kept = []
    for b in page.get_text("blocks"):
        if b[6] != 0 or not b[4].strip():
            continue
        br = fitz.Rect(b[:4])
        if any(wr.contains(br) for wr in white_rects):
            continue
        kept.append(b[4])
    return "\n".join(kept).strip()


def _image_rects(page):
    rects = []
    for img in page.get_images(full=True):
        try:
            rects.extend(page.get_image_rects(img[0]))
        except Exception:  # pragma: no cover - defensive against odd PDFs
            pass
    return rects


def _is_full_page(rect, page):
    return rect.width > page.rect.width * 0.85 and rect.height > page.rect.height * 0.85


def _non_embedded_fonts(page):
    bad = set()
    for f in page.get_fonts(full=True):
        # (xref, ext, type, basefont, name, encoding, referencer)
        ext, ftype, basefont = f[1], f[2], f[3]
        if ext == "n/a" and ftype != "Type3":
            bad.add(basefont or f[4])
    return sorted(bad)


def _apply_ignore(items, ignore_re):
    if not ignore_re:
        return list(items)
    return [i for i in items if not ignore_re.search(i)]


# --------------------------------------------------------------------------- #
# Side-by-side comparison PNG
# --------------------------------------------------------------------------- #

def render_comparison_pngs(doc_src, doc_tgt, out_dir: str, dpi: int = 110, pages=None):
    os.makedirs(out_dir, exist_ok=True)
    n = min(len(doc_src), len(doc_tgt))
    targets = pages if pages else range(1, n + 1)
    written = []
    gap = 24
    for pno in targets:
        if not 1 <= pno <= n:
            continue
        sp, tp = doc_src[pno - 1], doc_tgt[pno - 1]
        w1, h1, w2, h2 = sp.rect.width, sp.rect.height, tp.rect.width, tp.rect.height
        out = fitz.open()
        canvas = out.new_page(width=w1 + gap + w2, height=max(h1, h2))
        canvas.draw_rect(canvas.rect, color=None, fill=(1, 1, 1))
        canvas.show_pdf_page(fitz.Rect(0, 0, w1, h1), doc_src, pno - 1)
        canvas.show_pdf_page(fitz.Rect(w1 + gap, 0, w1 + gap + w2, h2), doc_tgt, pno - 1)
        x = w1 + gap / 2
        canvas.draw_line((x, 0), (x, canvas.rect.height), color=(0.8, 0, 0), width=1)
        path = os.path.join(out_dir, f"compare_page_{pno:03d}.png")
        canvas.get_pixmap(dpi=dpi).save(path)
        out.close()
        written.append(path)
    return written


def parse_pages(spec: str):
    """'1,3,5-7' -> [1,3,5,6,7]"""
    if not spec:
        return None
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        elif part:
            pages.append(int(part))
    return pages


# --------------------------------------------------------------------------- #
# Main audit
# --------------------------------------------------------------------------- #

def audit_document(src_path: str, tgt_path: str, strict: bool = False, json_out: str = None,
                   keywords_file: str = None, size_tol: float = 2.0, ignore: str = None,
                   check_numbers: bool = True, compare_png: str = None, compare_pages: str = None,
                   dpi: int = 110, quiet: bool = False):
    """Run the audit. Returns (passed: bool, report: dict)."""
    log = (lambda *a, **k: None) if quiet else print
    ignore_re = re.compile(ignore) if ignore else None
    keywords = load_keywords(keywords_file)

    log("=" * 70)
    log("  PDF-TRANSLATE AUTOMATED AUDIT ENGINE")
    log(f"  Source:     {src_path}")
    log(f"  Target:     {tgt_path}")
    log("=" * 70)

    for label, p in (("Source", src_path), ("Target", tgt_path)):
        if not os.path.exists(p):
            log(f"[FATAL] {label} PDF not found: {p}")
            return False, {"fatal": f"{label} PDF not found: {p}"}

    report = {
        "summary": {
            "source_pages": 0, "target_pages": 0, "pages_matched": False,
            "source_images": 0, "target_images": 0,
            "critical_errors": 0, "warnings": 0, "strict": strict,
        },
        "document_issues": [],
        "pages": [],
    }
    S = report["summary"]

    def doc_issue(sev, msg):
        report["document_issues"].append({"severity": sev, "message": msg})
        S["critical_errors" if sev == CRITICAL else "warnings"] += 1

    with fitz.open(src_path) as doc_src, fitz.open(tgt_path) as doc_tgt:
        n_src, n_tgt = len(doc_src), len(doc_tgt)
        S.update(source_pages=n_src, target_pages=n_tgt, pages_matched=(n_src == n_tgt))

        # ---- [1] page count -------------------------------------------------
        log("\n[1/4] PAGE COUNT CHECK:")
        if n_src == n_tgt:
            log(f"  ✔ PASS: Page count matches exactly ({n_src} pages).")
        else:
            log(f"  ✖ FAIL: Page count mismatch! Source={n_src}, Target={n_tgt}")
            doc_issue(CRITICAL, f"Page count mismatch: source={n_src}, target={n_tgt}")

        # ---- [2] asset integrity -------------------------------------------
        log("\n[2/4] VECTOR TEXT & ASSET INTEGRITY CHECK (Target PDF):")
        S["source_images"] = sum(len(_image_rects(p)) for p in doc_src)
        S["target_images"] = sum(len(_image_rects(p)) for p in doc_tgt)
        log(f"  Images placed: source={S['source_images']}, target={S['target_images']}")
        if S["source_images"] != S["target_images"]:
            log("  ▲ WARNING: Total image count differs (see per-page details).")

        # ---- [3] per page ---------------------------------------------------
        log("\n[3/4] PAGE-BY-PAGE 1:1 DEEP AUDIT:")
        for idx in range(max(n_src, n_tgt)):
            info = {"page_num": idx + 1, "status": "PASS", "issues": []}

            def add(sev, msg, _info=info):
                _info["issues"].append({"severity": sev, "message": msg})
                S["critical_errors" if sev == CRITICAL else "warnings"] += 1

            if idx >= n_src:
                add(CRITICAL, "Extra page beyond source document")
            elif idx >= n_tgt:
                add(CRITICAL, "Missing page present in source document")
            else:
                sp, tp = doc_src[idx], doc_tgt[idx]
                src_text = _visible_text(sp)
                tgt_text = _visible_text(tp)

                # page size
                dw, dh = abs(sp.rect.width - tp.rect.width), abs(sp.rect.height - tp.rect.height)
                if dw > size_tol or dh > size_tol:
                    add(CRITICAL, f"Page size mismatch: source {sp.rect.width:.1f}x{sp.rect.height:.1f}pt, "
                                  f"target {tp.rect.width:.1f}x{tp.rect.height:.1f}pt")

                # images
                s_imgs, t_imgs = _image_rects(sp), _image_rects(tp)
                src_full = any(_is_full_page(r, sp) for r in s_imgs)
                t_full = [r for r in t_imgs if _is_full_page(r, tp)]
                if t_full and not src_full:
                    add(CRITICAL, f"{len(t_full)} full-page raster image(s): target must be vector text, not a scan")
                if len(s_imgs) != len(t_imgs):
                    add(WARNING, f"Image count differs: source={len(s_imgs)}, target={len(t_imgs)}")
                else:
                    key = lambda r: (round(r.y0), round(r.x0))
                    for a, b in zip(sorted(s_imgs, key=key), sorted(t_imgs, key=key)):
                        if a.width > 0 and a.height > 0 and (
                                abs(a.width - b.width) / a.width > 0.05 or abs(a.height - b.height) / a.height > 0.05):
                            add(WARNING, f"Image size differs >5%: source {a.width:.1f}x{a.height:.1f}pt, "
                                         f"target {b.width:.1f}x{b.height:.1f}pt")

                # blank page
                if len(tgt_text) < 20 <= len(src_text):
                    add(WARNING, f"Suspiciously blank target page ({len(tgt_text)} chars, source {len(src_text)})")

                # broken glyphs
                if "\ufffd" in tgt_text:
                    add(CRITICAL, f"{tgt_text.count(chr(0xFFFD))} U+FFFD replacement char(s): missing glyphs / font issue")

                # fonts
                bad_fonts = _non_embedded_fonts(tp)
                if bad_fonts:
                    add(WARNING, f"Non-embedded font(s): {bad_fonts}")

                # placeholders / fabrications (source-aware)
                for kw in keywords:
                    if kw in tgt_text and kw not in src_text:
                        add(CRITICAL, f"Placeholder/fabrication phrase not present in source: '{kw}'")

                # clauses
                tgt_clauses = set(extract_clauses(tgt_text))
                missing = [c for c in extract_clauses(src_text) if c not in tgt_clauses]
                missing = _apply_ignore(missing, ignore_re)
                if missing:
                    add(WARNING, f"Missing clause numbers: {missing}")

                # structural refs
                missing_refs = sorted(extract_refs(src_text) - extract_refs(tgt_text))
                missing_refs = _apply_ignore(missing_refs, ignore_re)
                if missing_refs:
                    add(WARNING, f"Missing structural refs: {missing_refs}")

                # numbers
                if check_numbers:
                    missing_nums = sorted(extract_numbers(src_text) - extract_numbers(tgt_text),
                                          key=lambda x: (len(x), x))
                    missing_nums = _apply_ignore(missing_nums, ignore_re)
                    if missing_nums:
                        add(WARNING, f"Numbers in source not found in target: {missing_nums}")

            sevs = {i["severity"] for i in info["issues"]}
            info["status"] = "FAIL" if CRITICAL in sevs else ("WARNING" if WARNING in sevs else "PASS")
            if strict and info["status"] == "WARNING":
                info["status"] = "FAIL"
            report["pages"].append(info)

            icon = {"PASS": "✔", "WARNING": "▲", "FAIL": "✖"}[info["status"]]
            log(f"  Page {idx + 1:02d}: [{icon} {info['status']:7s}]")
            for it in info["issues"]:
                log(f"      - [{it['severity']}] {it['message']}")

        # ---- optional comparison PNGs --------------------------------------
        if compare_png:
            paths = render_comparison_pngs(doc_src, doc_tgt, compare_png, dpi=dpi, pages=parse_pages(compare_pages))
            report["comparison_pngs"] = paths
            log(f"\n  Side-by-side comparison PNGs ({len(paths)}) written to: {os.path.abspath(compare_png)}")

    # ---- [4] summary ---------------------------------------------------------
    log("\n[4/4] AUDIT SUMMARY:")
    log(f"  Total Critical Errors: {S['critical_errors']}")
    log(f"  Total Warnings:        {S['warnings']}" + ("  (strict: warnings count as failures)" if strict else ""))

    passed = S["critical_errors"] == 0 and (not strict or S["warnings"] == 0)
    S["passed"] = passed

    if json_out:
        os.makedirs(os.path.dirname(os.path.abspath(json_out)), exist_ok=True)
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        log(f"  Report exported to:    {json_out}")

    if passed:
        log("\n>>> AUDIT PASSED <<<" + ("" if S["warnings"] == 0 else "  (review warnings above)"))
    else:
        log("\n>>> AUDIT FAILED: Please review and fix the issues above! <<<")
    return passed, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit PDF translation quality and page-by-page alignment.")
    parser.add_argument("--src", required=True, help="Path to original source PDF")
    parser.add_argument("--tgt", required=True, help="Path to translated target PDF")
    parser.add_argument("--strict", action="store_true", help="Treat every WARNING as a failure (non-zero exit)")
    parser.add_argument("--json", "--json-out", dest="json", default=None,
                        help="Optional output path for JSON audit report")
    parser.add_argument("--keywords", default=None, help="Custom placeholder keyword JSON (default: scripts/keywords.json)")
    parser.add_argument("--size-tol", type=float, default=2.0, help="Page size tolerance in pt (default: 2)")
    parser.add_argument("--ignore", default=None,
                        help="Regex; clause numbers / refs / numbers matching it are not reported (e.g. '^(19|20)\\d\\d$')")
    parser.add_argument("--no-numbers", action="store_true", help="Disable numeric value diff")
    parser.add_argument("--compare-png", default=None, metavar="DIR", help="Write side-by-side source|target PNGs to DIR")
    parser.add_argument("--pages", default=None, help="Pages for --compare-png, e.g. '1,3,5-7' (default: all)")
    parser.add_argument("--dpi", type=int, default=110, help="DPI for --compare-png (default: 110)")
    args = parser.parse_args(argv)

    passed, _ = audit_document(args.src, args.tgt, strict=args.strict, json_out=args.json,
                               keywords_file=args.keywords, size_tol=args.size_tol, ignore=args.ignore,
                               check_numbers=not args.no_numbers, compare_png=args.compare_png,
                               compare_pages=args.pages, dpi=args.dpi)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
