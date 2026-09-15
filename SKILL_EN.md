---
name: pdf-translate
description: "Use when translating PDF documents between languages while strictly preserving original layout, formatting, typography, tables, and signatures. Powered by LLM direct comprehension, two-stage data-contract translation, chunked modular generation, in-browser JS overflow detection, and high-fidelity vector PDF reconstruction. Features zero-hallucination guardrails and automated 1:1 page-by-page audit script (audit_pdf.py)."
version: 2.2.0
author: Antigravity
---

# PDF Layout-Preserving Translation Skill (LLM Direct Translation + Vector Layout Reconstruction + Post-Generation Audit & Self-Healing)

Use this Skill when the user needs to **translate PDF documents** with strict requirements to **fully preserve original page layout, official letterheads, tables of contents, bilingual tables, and signature blocks**, ultimately outputting **publication-grade vector PDF files**.

> [!IMPORTANT]
> **Three Ironclad Rules (Eliminating Garbage Output, Long-Document Hallucinations, and Multi-Page Overflow)**:
> 1. **Strict Faithful Translation & Zero Hallucination**:
>    - **Never compress or omit clauses**: Faithfully translate every tier-1, tier-2, and tier-3 sub-clause (e.g., statutory qualification checklists 2.1.1~2.1.8, duration criteria, annual production capacity threshold 150,000 tons, binding requirements Volume 2A/2B, etc.). Subjective summaries or clause merges are strictly prohibited.
>    - **Never fabricate common-sense content**: Strictly prohibit inventing non-existent submission procedures, binding copies, bank credit facilities, or administrative workflows (e.g., if the original does not specify an amount, never invent 1,000,000 KWD; if Section 5.3 does not exist, never invent Section 5.3).
>    - **1:1 Faithful Table Reconstruction**: Official appendices (such as Appendix-1 through Appendix-6) must match column headers, row heights, checkboxes, remarks, and signature/stamp blocks 1:1. Never substitute with self-invented "Checklists" or generic makeshift tables.
> 2. **Schema-First & Chunked Pipeline**:
>    - **Decouple data from layout**: For long documents, extract structured page data (clause trees, parameter dictionaries, table rows/columns) before injecting into standardized HTML templates. Never generate freeform long-form text while concurrently writing markup.
>    - **Single batch must not exceed 10 pages**: Documents exceeding 10 pages must be split into modular units of 10 pages each (e.g., `part1_pages.py`, `part2_pages.py`) to prevent LLM attention degradation and hallucinations in later sections.
> 3. **Mandatory Automated Audit with `audit_pdf.py`**:
>    - Once the PDF is rendered, **it must never be delivered directly to the user**. The built-in `scripts/audit_pdf.py` must be executed to perform comprehensive checks on page count, vector layers, clause symmetric diffs, and hallucination keywords.
>    - Any omission, clause mismatch, numerical error, or fabricated item triggers an automated Self-Repair loop until all checks PASS.

---

## Trigger Scenarios

- User provides or specifies a PDF file requesting translation to Chinese, English, or other languages.
- User explicitly requests "preserve original layout", "maintain formatting", or "output as PDF".
- Official bidding documents, commercial contracts, prequalification brochures (e.g., Middle East tender documents, Ministry of Electricity & Water & Renewable Energy MEWRE, water pipeline engineering).
- Complex documents featuring mixed Arabic/English/Chinese typography, bilingual comparison tables, signature/stamp blocks, and dotted leader tables of contents.
- Industry technical specifications, academic papers, enterprise whitepapers.

---

## Agent Standard Operating Procedure (SOP)

When assigned a PDF translation task, the Agent must strictly adhere to the following 5-step closed-loop workflow:

### Step 1: Document Inspection & Chunking Plan
Use Python (`fitz` / PyMuPDF) to inspect total page count, section hierarchy, and special layout elements:
```python
import fitz
doc = fitz.open("path/to/document.pdf")
print("Total pages:", len(doc))
# Analyze page text structures, tables, dual-column headers, TOC dotted leaders, and footer signature blocks
# If total pages > 10, establish a modular chunking plan (e.g., Part 1: P1~10, Part 2: P11~20 ...)
```

### Step 2: Two-Stage Strict Translation (Zero Hallucination)
- **Stage 1 (Extraction & Verification)**: Extract clause numbers, numerical ranges, and table fields on a page-by-page basis to establish a strict translation data contract.
- **Stage 2 (Template Population)**:
  - Accurately translate international standards (e.g., ISO 2531, BS EN 545, AWWA, ISO 17020/17025) and agency-specific terminology (e.g., Kuwait MEWRE, ductile iron pipes, fittings, restrained push-on joints, double-thickness cement mortar lining).
  - 100% verify numbers and units (e.g., 200.00 ppm, 4°C, 150 microns, 2200 kg/cm²).

### Step 3: High-Fidelity Vector Layout Reconstruction & Height Guard
Use modern HTML5 + CSS `@page` print styles for 1:1 page mapping:
- **Physical Height Bound & Anti-Overflow**:
  ```css
  @page {
    size: A4 portrait;
    margin: 12mm 15mm 12mm 15mm;
  }
  .page {
    page-break-after: always;
    height: 270mm;
    max-height: 270mm;
    position: relative;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Strictly prevent internal elements from expanding height and triggering unwanted blank pages */
  }
  .content-area {
    flex: 1;
    overflow: hidden;
  }
  ```
- **Official Dual-Column Headers**: Reconstruct official bilingual two-column header frames (e.g., English on the left, target language on the right), preserving document reference codes like `MEWRE/W.P.S.2026`.
- **TOC Dotted Leaders**: Use Flexbox and `border-bottom: 1.2px dotted #555` to achieve pixel-perfect alignment between titles and page numbers.
- **Tables & Signatures**: Preserve all grid borders, multi-row spans, signature/stamp areas, and undertaking statement boxes.
- **Typography Standards**: Use standard high-legibility vector fonts (`font-family: "SimSun", "Songti SC", "Microsoft YaHei", serif;` or `Times New Roman, Arial, sans-serif`), guaranteeing crisp rendering and zero garbled characters.

### Step 4: Headless Vector Rendering & JS Height Overflow Probe
Execute the built-in Playwright rendering script to generate the publication-grade vector PDF. An injected JavaScript probe automatically verifies whether any page exceeds its bounding box:
```powershell
python "scripts/render_pdf.py" "path/to/full_doc.html" "path/to/output_full.pdf"
```

### Step 5: One-Click Automated Audit & Self-Healing Loop
After generating the PDF, **the built-in `audit_pdf.py` script must be executed**:
```powershell
python "scripts/audit_pdf.py" --src "path/to/source.pdf" --tgt "path/to/output_full.pdf"
```

The audit tool executes four automated pipelines:
1. **1:1 Page Count Verification**: Source and target document page counts must match exactly.
2. **Pure Vector Layer Check**: Raster image count must be 0 (preventing screenshot/scan fakery).
3. **Clause Symmetric Diff**: Scans clause IDs (e.g., 1.1~1.4, 2.1.1~2.1.8) page-by-page, flagging omissions or hallucinated extra clauses.
4. **AI Hallucination & Evasion Keyword Radar**: Automatically blocks phrases like "Technical Summary", "Checklist", "TBD", "Omitted due to space", "Refer to English original", etc.

**Self-Repair Loop**: If `audit_pdf.py` flags any Critical Error, immediately edit the corresponding chunk's HTML, re-render, and re-audit until all checks PASS before final delivery!

---

## Built-in Scripts

- **Vector PDF Rendering Engine (with JS Page Overflow Probe)**:
  [`scripts/render_pdf.py`](scripts/render_pdf.py)
  - Leverages Chromium / Edge headless vector print engine to measure `.page` physical heights in milliseconds, preventing multi-page overflow.
- **PDF 1:1 Automated Audit Engine**:
  [`scripts/audit_pdf.py`](scripts/audit_pdf.py)
  - Page-by-page 1:1 inspection comparing source and target PDFs across page alignment, vector integrity, clause diffs, numerical accuracy, and anti-hallucination radar.
