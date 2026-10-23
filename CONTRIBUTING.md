# Contributing to PDF-Translate

Thank you for your interest in improving **PDF-Translate**!

## How to Contribute

1. **Fork the repository** on GitHub.
2. **Create a topic branch**: `git checkout -b feature/my-feature`.
3. **Install dev dependencies**: `pip install -r requirements-dev.txt && playwright install chromium`.
4. **Make your changes** and test thoroughly:
   - `python -m pytest` (unit + integration tests, including deliberately defective translations)
   - `python examples/quick_demo.py` (end-to-end render + audit)
5. **Commit your changes**: `git commit -m "feat: add support for XYZ"`.
6. **Push to your fork**: `git push origin feature/my-feature`.
7. **Open a Pull Request** against the `main` branch.

## Code Standards
- Ensure Python scripts are formatted cleanly and include UTF-8 console compatibility for Windows.
- Preserve the unified page convention (`@page { margin: 0 }`, one `.page` = one physical sheet) and the recursive overflow probe.
- Keep `audit_pdf.py` zero-dependency outside the standard library and `fitz` (PyMuPDF).
- Every new audit check must come with a test in `tests/test_audit.py` that builds a defective PDF and asserts it is caught.
