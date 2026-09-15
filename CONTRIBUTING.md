# Contributing to PDF-Translate

Thank you for your interest in improving **PDF-Translate**!

## How to Contribute

1. **Fork the repository** on GitHub.
2. **Create a topic branch**: `git checkout -b feature/my-feature`.
3. **Make your changes** and test thoroughly using `python examples/quick_demo.py`.
4. **Commit your changes**: `git commit -m "feat: add support for XYZ"`.
5. **Push to your fork**: `git push origin feature/my-feature`.
6. **Open a Pull Request** against the `main` branch.

## Code Standards
- Ensure Python scripts are formatted cleanly and include UTF-8 console compatibility for Windows.
- Always verify that the physical height constraints (`.page` CSS max-height) and anti-overflow probes are preserved.
- Keep `audit_pdf.py` zero-dependency outside standard library and `fitz` (PyMuPDF).
