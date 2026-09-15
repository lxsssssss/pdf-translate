# -*- coding: utf-8 -*-
"""
Quick Demo Script for PDF-Translate Skill
Demonstrates rendering an HTML layout to vector PDF and running the audit engine.
"""

import os
import sys
import subprocess

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
RENDER_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "render_pdf.py")
AUDIT_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "audit_pdf.py")

SAMPLE_HTML = os.path.join(SCRIPT_DIR, "sample_doc.html")
OUTPUT_PDF = os.path.join(SCRIPT_DIR, "output_demo.pdf")

def main():
    print("=" * 60)
    print("  🚀 PDF-Translate Quick Start Demo")
    print("=" * 60)

    # Step 1: Render HTML to Vector PDF
    print("\n[Step 1/2] Rendering HTML template to vector PDF via Playwright...")
    render_cmd = [sys.executable, RENDER_SCRIPT, SAMPLE_HTML, OUTPUT_PDF, "--strict-overflow"]
    ret = subprocess.run(render_cmd)
    if ret.returncode != 0:
        print("[FAIL] Render step failed. Please ensure playwright is installed (`playwright install chromium`).")
        sys.exit(1)

    # Step 2: Audit the generated PDF
    print("\n[Step 2/2] Running automated audit engine on the rendered PDF...")
    audit_cmd = [sys.executable, AUDIT_SCRIPT, "--src", OUTPUT_PDF, "--tgt", OUTPUT_PDF]
    ret = subprocess.run(audit_cmd)

    if ret.returncode == 0:
        print("\n" + "=" * 60)
        print("  🎉 DEMO SUCCESSFUL!")
        print(f"  Vector PDF generated at: {OUTPUT_PDF}")
        print("=" * 60)
    else:
        print("[FAIL] Audit step failed.")
        sys.exit(ret.returncode)

if __name__ == "__main__":
    main()
