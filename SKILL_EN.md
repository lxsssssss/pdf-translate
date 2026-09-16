---
name: pdf-translate
description: "Use when translating PDF documents between languages while strictly preserving original layout, formatting, typography, tables, and signatures. Powered by LLM direct comprehension, two-stage data-contract translation, chunked modular generation, in-browser JS overflow detection, and high-fidelity vector PDF reconstruction. Features zero-hallucination guardrails and automated 1:1 page-by-page audit script (audit_pdf.py)."
version: 2.3.0
author: Antigravity
---

# PDF Layout-Preserving Translation Skill (LLM Direct Translation + Geometry Probe Measurement + Vector Layout Reconstruction + Post-Generation Audit & Self-Healing)

Use this Skill when the user needs to **translate PDF documents** with strict requirements to **fully preserve original page layout, official letterheads, tables of contents, bilingual tables, signature blocks, and exact figure dimensions**, ultimately outputting **publication-grade vector PDF files**.

> [!IMPORTANT]
> **Four Ironclad Rules (Eliminating Garbage Output, Long-Document Hallucinations, Multi-Page Overflow, and Figure Distortion)**:
> 1. **Strict Faithful Translation & Zero Hallucination**:
>    - **Never compress or omit clauses**: Faithfully translate every tier-1, tier-2, and tier-3 sub-clause (e.g., statutory qualification checklists 2.1.1~2.1.8, duration criteria, annual production capacity threshold 150,000 tons, binding requirements Volume 2A/2B, etc.). Subjective summaries or clause merges are strictly prohibited.
>    - **Never fabricate common-sense content**: Strictly prohibit inventing non-existent submission procedures, binding copies, bank credit facilities, or administrative workflows (e.g., if the original does not specify an amount, never invent 1,000,000 KWD; if Section 5.3 does not exist, never invent Section 5.3).
>    - **1:1 Faithful Table Reconstruction**: Official appendices (such as Appendix-1 through Appendix-6) must match column headers, row heights, checkboxes, remarks, and signature/stamp blocks 1:1. Never substitute with self-invented "Checklists" or generic makeshift tables.
> 2. **Geometry Probe & Visual Anchor Measurement First**:
>    - **Never guess dimensions empirically**: Never apply arbitrary CSS constraints such as `max-height: 220px` without inspecting original PDF geometry, which severely shrinks and distorts embedded diagrams.
>    - **Extract physical coordinates & rects 1:1**: When extracting figures, always call `page.get_image_rects(xref)` to obtain actual `width`, `height`, and `x0, y0` coordinates, rendering them at exact physical dimensions in HTML (e.g., `width: 218.9pt; height: 322.4pt;`).
>    - **Faithful geometric line and rule replication**: Use `page.get_drawings()` to extract all geometric rules and divider bars (such as the 4pt top rule and 1pt bottom rule around paper titles, or 143.5pt left-aligned short footnote dividers), never substituting them with generic 100% border rules.
>    - **Chinese information density compensation & vertical baseline alignment**: Chinese text density is 20%~35% higher than English. Record key vertical anchor baselines `y0` (such as abstract title, abstract body, section starts, and footnote dividers). Use balanced line-heights (`1.35~1.45`), margin tuning, and grid/absolute anchors to prevent conspicuous lower-half blank voids.
>    - **First-page header/footer conventions**: Most top academic conferences (NIPS, ICML, CVPR) and official executive summaries do not display a page number on Page 1, placing conference copyright notices at the bottom instead. Never blindly add page number "1" to the cover page.
> 3. **Schema-First & Chunked Pipeline**:
>    - **Decouple data from layout**: For long documents, extract structured page data (clause trees, parameter dictionaries, table rows/columns) before injecting into standardized HTML templates. Never generate freeform long-form text while concurrently writing markup.
>    - **Single batch must not exceed 10 pages**: Documents exceeding 10 pages must be split into modular units of 10 pages each (e.g., `part1_pages.py`, `part2_pages.py`) to prevent LLM attention degradation and hallucinations in later sections.
> 4. **Mandatory Automated Audit & User Preview Gate Before Commit**:
>    - Once the PDF is rendered, **it must never be delivered directly to the user**. The built-in `scripts/audit_pdf.py` must be executed to perform comprehensive checks on page count, vector layers, clause symmetric diffs, and hallucination keywords.
>    - Side-by-side comparison images (PNG) **must be rendered and displayed directly in the chat for user review and inspection**. Never execute Git commit or push until the user explicitly confirms satisfaction!

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

### Step 1: Document Inspection & Geometry Probing
Use Python (`fitz` / PyMuPDF) to comprehensively inspect document physical dimensions, figure bounding boxes, geometric rules, and text baseline anchors:
```python
import fitz
doc = fitz.open("path/to/document.pdf")
print("Total pages:", len(doc))

for i, page in enumerate(doc):
    print(f"\n=== PAGE {i+1} rect: {page.rect} ===")
    # 1. Probe image physical dimensions and locations
    for img in page.get_images():
        for r in page.get_image_rects(img[0]):
            print(f"  Image xref {img[0]}: w={r.width:.1f}, h={r.height:.1f}, (x0={r.x0:.1f}, y0={r.y0:.1f})")
    # 2. Probe geometric lines and rule borders
    for d in page.get_drawings():
        r = d['rect']
        if r.width > 30:
            print(f"  Line: w={r.width:.1f}, h={r.height:.1f}, (x0={r.x0:.1f}, y0={r.y0:.1f})")
    # 3. Probe text block baseline origins y0
    for b in page.get_text("blocks"):
        if b[4].strip():
            print(f"  Block ({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}): {b[4].strip()[:40]}")
# If total pages > 10, establish a modular chunking plan (e.g., Part 1: P1~10, Part 2: P11~20 ...)
```

### Step 2: Two-Stage Strict Translation (Zero Hallucination)
- **Stage 1 (Extraction & Verification)**: Extract clause numbers, numerical ranges, and table fields on a page-by-page basis to establish a strict translation data contract.
- **Stage 2 (Template Population)**:
  - Accurately translate technical terminology and international standards (e.g., Transformer self-attention, encoder-decoder stacks, BLEU scores, residual connections; or ISO 2531, BS EN 545, AWWA, Kuwait MEWRE).
  - 100% verify numbers, units, and mathematical equations (e.g., 200.00 ppm, 4°C, 150 microns, 2200 kg/cm², $d_{\text{model}} = 512$).

### Step 3: High-Fidelity Vector Layout Reconstruction & Physical Anchors
Use modern HTML5 + CSS `@page` print styles for 1:1 page mapping:
- **Dynamic Physical Dimensions & Anti-Overflow**:
  Configure `@page` according to measured physical dimensions (e.g., US Letter `size: 8.5in 11in;` or A4 `size: 210mm 297mm;`):
  ```css
  @page {
    size: 8.5in 11in;
    margin: 0;
  }
  .page {
    width: 8.5in;
    height: 11in;
    max-height: 11in;
    padding: 72pt 108pt 72pt 108pt;
    page-break-after: always;
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
- **1:1 Image Dimensions**: Explicitly set image `width` and `height` based on Step 1 measurements (e.g., `width: 218.9pt; height: 322.4pt;`), never guessing with empirical clamps.
- **Geometric Rule Reconstruction**: Reproduce exact stroke widths and lengths (e.g., title 4pt top rule + 1pt bottom rule, 143.5pt short footnote divider).
- **Chinese Baseline Compensation**: Distribute vertical space harmoniously using comfortable line-heights (`1.35~1.45`) and paragraph margins matching original section origins.
- **Typography Standards**: Use publication-grade serif fonts (Times New Roman for English, SimSun / Songti SC for Chinese), ensuring mathematical clarity and zero garbled glyphs.

### Step 4: Headless Vector Rendering & JS Height Overflow Probe
Execute the built-in Playwright rendering script to generate the publication-grade vector PDF. An injected JavaScript probe automatically verifies whether any page exceeds its bounding box:
```powershell
python "scripts/render_pdf.py" "path/to/full_doc.html" "path/to/output_full.pdf"
```

### Step 5: Automated Audit & Visual Review Gate
After generating the PDF, **the built-in `audit_pdf.py` script must be executed**:
```powershell
python "scripts/audit_pdf.py" --src "path/to/source.pdf" --tgt "path/to/output_full.pdf"
```

The audit tool executes four automated pipelines:
1. **1:1 Page Count Verification**: Source and target document page counts must match exactly.
2. **Pure Vector Layer Check**: Preserved vector asset count matches source exactly.
3. **Clause & Entity Symmetric Diff**: Scans clause IDs, table names, and figure titles page-by-page, flagging omissions.
4. **AI Hallucination & Evasion Keyword Radar**: Automatically blocks phrases like "Technical Summary", "Checklist", "TBD", "Omitted due to space", "Refer to English original", etc.

**User Visual Review Gate**:
- Render 1:1 side-by-side comparison images (PNG) and present key pages (cover, architecture diagrams, complex tables) directly in the conversation.
- Report audit results and alignment metrics. **Always wait for explicit user confirmation before committing to Git or concluding the task**!

---

## Built-in Scripts

- **Vector PDF Rendering Engine (with JS Page Overflow Probe)**:
  [`scripts/render_pdf.py`](scripts/render_pdf.py)
  - Leverages Chromium / Edge headless vector print engine to measure `.page` physical heights in milliseconds, preventing multi-page overflow.
- **PDF 1:1 Automated Audit Engine**:
  [`scripts/audit_pdf.py`](scripts/audit_pdf.py)
  - Page-by-page 1:1 inspection comparing source and target PDFs across page alignment, vector integrity, clause diffs, numerical accuracy, and anti-hallucination radar.
