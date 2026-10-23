# -*- coding: utf-8 -*-
"""
Helper script for rendering HTML to a publication-grade vector PDF using Playwright (Edge/Chromium).
Ensures zero raster images, selectable text, exact page layout, and automated page overflow detection.

Overflow probe checks:
  * every `.page` container AND every descendant with clipping overflow (hidden/clip/auto/scroll),
    so content clipped by nested wrappers such as `.content-area { overflow: hidden }` is still caught;
  * both vertical and horizontal overflow;
  * the number of `.page` containers vs. the number of pages in the generated PDF.
"""

import sys
import os
import argparse
import pathlib

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
except ImportError:
    print("Error: playwright is required. Install via `pip install playwright && playwright install chromium`")
    sys.exit(1)

# Tolerance (CSS px) for sub-pixel rounding
TOLERANCE_PX = 2

OVERFLOW_CHECK_JS = """
(tol) => {
    const CLIP = new Set(['hidden', 'clip', 'auto', 'scroll']);
    const describe = (el) => {
        let s = el.tagName.toLowerCase();
        if (el.id) s += '#' + el.id;
        if (el.classList.length) s += '.' + Array.from(el.classList).join('.');
        return s;
    };
    const pages = document.querySelectorAll('.page');
    const errors = [];
    pages.forEach((pageEl, index) => {
        const candidates = [pageEl, ...pageEl.querySelectorAll('*')];
        for (const el of candidates) {
            const cs = getComputedStyle(el);
            const clipsY = el === pageEl || CLIP.has(cs.overflowY);
            const clipsX = el === pageEl || CLIP.has(cs.overflowX);
            const dy = el.scrollHeight - el.clientHeight;
            const dx = el.scrollWidth - el.clientWidth;
            if (clipsY && el.clientHeight > 0 && dy > tol) {
                errors.push({page: index + 1, element: describe(el), axis: 'vertical',
                             scroll: el.scrollHeight, client: el.clientHeight, overflowPx: dy});
            }
            if (clipsX && el.clientWidth > 0 && dx > tol) {
                errors.push({page: index + 1, element: describe(el), axis: 'horizontal',
                             scroll: el.scrollWidth, client: el.clientWidth, overflowPx: dx});
            }
        }
    });
    return {pageCount: pages.length, errors};
}
"""


def _launch_browser(p, browser_choice: str):
    """Launch the requested browser; 'auto' tries msedge first then falls back to bundled chromium."""
    order = {"auto": ["msedge", None], "msedge": ["msedge"], "chrome": ["chrome"], "chromium": [None]}[browser_choice]
    last_err = None
    for channel in order:
        try:
            kwargs = {"headless": True}
            if channel:
                kwargs["channel"] = channel
            browser = p.chromium.launch(**kwargs)
            print(f"Launched browser: {channel or 'chromium (bundled)'}")
            return browser
        except PlaywrightError as e:
            last_err = e
    raise RuntimeError(f"Unable to launch any browser ({browser_choice}). "
                       f"Run `playwright install chromium`. Last error: {last_err}")


def _count_pdf_pages(pdf_path: str):
    try:
        import fitz  # PyMuPDF (optional here)
    except ImportError:
        return None
    with fitz.open(pdf_path) as doc:
        return len(doc)


def render_html_to_pdf(html_path: str, output_pdf_path: str, strict_overflow: bool = False,
                       browser_choice: str = "auto", fallback_format: str = "A4") -> bool:
    """Render HTML to PDF. Returns True when no overflow / page-count problems were detected."""
    html_abs = os.path.abspath(html_path)
    output_abs = os.path.abspath(output_pdf_path)

    if not os.path.exists(html_abs):
        raise FileNotFoundError(f"HTML file not found: {html_abs}")

    os.makedirs(os.path.dirname(output_abs), exist_ok=True)
    ok = True

    print("Launching Playwright for vector PDF rendering...")
    with sync_playwright() as p:
        browser = _launch_browser(p, browser_choice)
        try:
            page = browser.new_context().new_page()

            # Load page and wait until all network assets are idle
            page.goto(pathlib.Path(html_abs).as_uri(), wait_until="networkidle")

            # Wait for all web fonts to load (return a serialisable value)
            page.evaluate("() => document.fonts.ready.then(() => true)")

            result = page.evaluate(OVERFLOW_CHECK_JS, TOLERANCE_PX)
            page_containers = result["pageCount"]
            overflows = result["errors"]

            if page_containers == 0:
                print("  ▲ WARNING: No `.page` containers found; overflow probe skipped.")
            elif overflows:
                ok = False
                bad_pages = sorted({o["page"] for o in overflows})
                print(f"\n[WARNING] Detected content overflow in {len(bad_pages)} page(s): {bad_pages}")
                for ov in overflows:
                    print(f"  ✖ Page {ov['page']} <{ov['element']}> {ov['axis']}: "
                          f"scroll={ov['scroll']}px > client={ov['client']}px (+{ov['overflowPx']}px)")
            else:
                print(f"  ✔ PASS: All {page_containers} .page containers (incl. nested clipping boxes) "
                      f"satisfy physical bounds.")

            if strict_overflow and not ok:
                print("\n[FAIL] Strict overflow check failed! Content exceeded its bounding box; PDF not written.")
                return False

            # Print PDF with high-fidelity vector settings; CSS @page size takes precedence
            page.pdf(
                path=output_abs,
                format=fallback_format,
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
            )
        finally:
            browser.close()

    pdf_pages = _count_pdf_pages(output_abs)
    if pdf_pages is not None and page_containers and pdf_pages != page_containers:
        ok = False
        print(f"  ✖ FAIL: PDF has {pdf_pages} pages but HTML has {page_containers} .page containers "
              f"(check .page height vs. @page size/margin).")
    elif pdf_pages is not None:
        print(f"  ✔ PASS: PDF page count ({pdf_pages}) matches .page containers.")

    print(f"Generated vector PDF at:\n{output_abs}")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render HTML to publication-grade vector PDF.")
    parser.add_argument("html", help="Path to input HTML file")
    parser.add_argument("pdf", help="Path to output PDF file")
    parser.add_argument("--strict-overflow", action="store_true",
                        help="Fail (exit 2) if any page overflows or page count mismatches")
    parser.add_argument("--browser", choices=["auto", "msedge", "chrome", "chromium"], default="auto",
                        help="Browser to use (default: auto = msedge, fallback to bundled chromium)")
    parser.add_argument("--format", default="A4",
                        help="Fallback paper format when HTML has no CSS @page size (default: A4)")

    args = parser.parse_args()
    try:
        success = render_html_to_pdf(args.html, args.pdf, strict_overflow=args.strict_overflow,
                                     browser_choice=args.browser, fallback_format=args.format)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[FATAL] {e}")
        sys.exit(1)
    sys.exit(0 if success or not args.strict_overflow else 2)
