# PR Submission Guide for `PatrickJS/awesome-cursorrules`

- **Target Repository**: [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)
- **Contribution Type**: Add `.mdc` file to `rules/` + Add listing link to `README.md`
- **Target Category in README.md**: `### Documentation` (in alphabetical order)

---

### File 1: Create `rules/pdf-translate-layout-preserving-cursorrules-prompt-file.mdc`

```markdown
---
description: "Cursor rules for 1:1 layout-preserving vector PDF translation, anti-overflow CSS typography checks, and automated page difference audits."
globs: **/*.py,**/*.html,**/*.pdf,**/.cursorrules,**/SKILL.md
alwaysApply: false
---
# PDF Translate — Layout-Preserving Translation & Visual Audit Rules

Cursor rules for translating documents (PDFs, HTML reports, documentation) between languages while strictly preserving original layout, typography, tables, and visual structure.

Source repo: https://github.com/lxsssssss/pdf-translate

## Core Principles

1. **Strict 1:1 Page-to-Page Layout Preservation**:
   - Translate modularly page-by-page. Never merge pages or allow content to shift page boundaries.
   - Use CSS `@page { size: A4; margin: 0; }` with explicit pixel/millimeter height bounds.

2. **Two-Stage Architecture (Layout First, Content Second)**:
   - Stage 1: Parse structure, extract text tokens, bounding boxes, styles, and background vector assets.
   - Stage 2: Translate text content into a strict JSON data-contract matching the structural tokens.

3. **In-Browser Anti-Overflow Checks**:
   - When text expands after translation (e.g. English -> Russian or German), use JavaScript probes (`scrollWidth > clientWidth` or `scrollHeight > clientHeight`).
   - Dynamically adjust `font-size` or `letter-spacing` within bounds (min 70% of original size) before rendering.

4. **Zero-Hallucination Guardrails**:
   - Preserve all numeric values, URLs, code snippets, variables, and technical terms unaltered.
   - Mark ambiguous domain terms in an audit log rather than guessing.

5. **Automated Visual Difference Auditing**:
   - Run page-by-page visual audits comparing original vs translated vector renderings using `audit_pdf.py`.
   - Any pixel discrepancy beyond standard font expansion triggers layout reflow review.
```

---

### File 2: In `README.md` under `### Documentation`

Locate `### Documentation` (around line 352):
```markdown
### Documentation

- [Gherkin Style Testing](https://github.com/PatrickJS/awesome-cursorrules/blob/main/rules/gherkin-style-testing-cursorrules-prompt-file.mdc) - Behavior-driven scenarios and acceptance criteria.
- [How-To Documentation](https://github.com/PatrickJS/awesome-cursorrules/blob/main/rules/how-to-documentation-cursorrules-prompt-file.mdc) - Task-oriented guides and procedural documentation.
- [PDF & Document Translation (Layout-Preserving)](https://github.com/PatrickJS/awesome-cursorrules/blob/main/rules/pdf-translate-layout-preserving-cursorrules-prompt-file.mdc) - 1:1 layout-preserving vector PDF translation and automated page audit rules.
- [README Best Practices](https://github.com/PatrickJS/awesome-cursorrules/blob/main/rules/readme-best-practices-cursorrules-prompt-file.mdc) - README documentation with best practices integration.
```

---

### PR Title:
```text
Add PDF & Document Translation (Layout-Preserving) rule
```

### PR Description:
```markdown
### Summary
Added a new Cursor Project Rule (`.mdc`) for layout-preserving vector PDF translation, anti-overflow CSS checks, and automated 1:1 visual audits.

- **Rule file**: `rules/pdf-translate-layout-preserving-cursorrules-prompt-file.mdc`
- **README listing**: Added under `### Documentation` in alphabetical order
- **Source repository**: https://github.com/lxsssssss/pdf-translate
```

