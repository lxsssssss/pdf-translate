# -*- coding: utf-8 -*-
"""
Quick Demo Script for PDF-Translate Skill

End-to-end demo on a real source -> translation pair:
  1. Render the English original  (examples/sample_source.html) to PDF
  2. Render the Chinese translation (examples/sample_doc.html)   to PDF with --strict-overflow
  3. Audit translation against the source and write side-by-side comparison PNGs
"""

import os
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
RENDER_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "render_pdf.py")
AUDIT_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "audit_pdf.py")

SOURCE_HTML = os.path.join(SCRIPT_DIR, "sample_source.html")
TARGET_HTML = os.path.join(SCRIPT_DIR, "sample_doc.html")
OUT_DIR = os.path.join(SCRIPT_DIR, "output")
SOURCE_PDF = os.path.join(OUT_DIR, "source_demo.pdf")
TARGET_PDF = os.path.join(OUT_DIR, "output_demo.pdf")
COMPARE_DIR = os.path.join(OUT_DIR, "compare_png")


def run(cmd, label):
    print(f"\n{label}")
    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        print(f"[FAIL] {label.strip()} (exit {ret.returncode})")
        sys.exit(ret.returncode)


def main():
    print("=" * 60)
    print("  📄 PDF-Translate Quick Start Demo")
    print("=" * 60)

    run([sys.executable, RENDER_SCRIPT, SOURCE_HTML, SOURCE_PDF],
        "[Step 1/3] Rendering source (English original) to vector PDF...")
    run([sys.executable, RENDER_SCRIPT, TARGET_HTML, TARGET_PDF, "--strict-overflow"],
        "[Step 2/3] Rendering translation to vector PDF (strict overflow probe)...")
    run([sys.executable, AUDIT_SCRIPT, "--src", SOURCE_PDF, "--tgt", TARGET_PDF,
         "--json", os.path.join(OUT_DIR, "audit_report.json"), "--compare-png", COMPARE_DIR],
        "[Step 3/3] Auditing translation against source...")

    print("\n" + "=" * 60)
    print("  ✅ DEMO SUCCESSFUL!")
    print(f"  Translated PDF:   {TARGET_PDF}")
    print(f"  Comparison PNGs:  {COMPARE_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
