---
name: pdf-translate
description: "Use when translating PDF documents between languages while strictly preserving original layout, formatting, typography, tables, and signatures. Powered by LLM direct comprehension, two-stage data-contract translation, chunked modular generation, in-browser JS overflow detection, and high-fidelity vector PDF reconstruction. Features zero-hallucination guardrails and automated 1:1 page-by-page audit script (audit_pdf.py)."
version: 2.2.0
author: Antigravity
---

# PDF 保持原排版翻译 Skill (大模型直译 + 矢量排版重构 + 生成后对比自愈)

当用户需要**翻译 PDF 文档**，且要求**必须完整保留原始版面格式、公文表头、目录、双语表格、签章栏**并最终**输出为高保真矢量 PDF 文件**时，使用此 Skill。

> [!IMPORTANT]
> **三大核心铁律（杜绝机翻乱码、长文档幻觉与跨页溢出）**：
> 1. **严禁脑补，严格忠实直译 (Strict Faithful Translation & Zero Hallucination)**：
>    - **不得压缩或遗漏条款**：逐条忠实翻译每一个一级、二级、三级子条款（如法定资质证照清单 2.1.1~2.1.8、年限指标、年产能门槛 150,000 吨、分卷装订规则 Volume 2A/2B 等），坚决禁止主观总结或合并条款；
>    - **坚决禁止虚构常识**：严禁凭常识脑补原文不存在的交付程序、装订份数、银行授信金额或办事流程（例如原文未写具体金额则绝对禁止编造 1,000,000 KWD，无 5.3 节则绝对不可添加 5.3 节）；
>    - **表格格式 1:1 忠实还原**：官方附表（如 Appendix-1 至 Appendix-6）的列名、行高、选项框、备注及签字盖章区必须严格对齐原件，严禁用自创的“申报核对清单 (Checklist)”或通用表格粗糙代替。
> 2. **两阶段解耦与分块生成 (Schema-First & Chunked Pipeline)**：
>    - **数据与排版分离**：长文档翻译时，优先提取页面结构化数据（条款清单、参数字典、表格行列），再灌入标准化 HTML 模板，严禁一边长篇自由发挥一边写标签；
>    - **单批次生成严禁超过 10 页**：超过 10 页的文档强制按 10 页为单位拆分为独立模块（如 `part1_pages.py`, `part2_pages.py`），避免模型在中后段注意力衰减导致失控。
> 3. **生成后必须执行自动化对比检查 (Mandatory Automated Audit with audit_pdf.py)**：
>    - PDF 渲染生成后，**绝不允许直接交付给用户**，必须运行技能内置的 `scripts/audit_pdf.py` 执行页码、矢量层、条款差集与敏感词全面扫描；
>    - 发现任何遗漏、编号不匹配、数字错误或虚构项，必须触发自动重修（Self-Repair），校验通过后方可交付。

---

## 触发场景 (Trigger Scenarios)

- 用户提供或指定 PDF 文件，要求翻译为中文、英文或其他语言；
- 用户明确要求“**保持原排版**”、“**格式不变**”、“**输出为 PDF**”；
- 官方招标文件、商务合同、投标预审资格手册（如中东阿文/英文标书、水电部 MEWRE、管网工程）；
- 包含中英阿多语言混排、双语对照表格、签字盖章区、点线对齐目录的复杂 PDF 文档；
- 行业技术规范、学术论文、企业白皮书。

---

## Agent 执行标准工作流 (Standard Operating Procedure)

当收到翻译 PDF 任务时，Agent 需严格遵循以下 5 步标准化闭环作业流程：

### 第一步：文档结构探测与分块规划 (Inspection & Chunking Plan)
使用 Python (`fitz` / PyMuPDF) 探测文档总页数、章节划分与特殊排版元素：
```python
import fitz
doc = fitz.open("path/to/document.pdf")
print("Total pages:", len(doc))
# 分析各页面文本结构、表格、双栏表头、目录点线与页脚签章栏
# 若总页数 > 10 页，强制制定分块规划（如 Part 1: P1~10, Part 2: P11~20 ...）
```

### 第二步：两阶段专业直译（严格无脑补）(Two-Stage Strict Translation)
- **阶段 1（提取与核定）**：先按页提取条款编号、所有数值区间与表格字段，建立精确的翻译数据契约；
- **阶段 2（模板化填装）**：
  - 准确翻译国际标准（如 ISO 2531、BS EN 545、AWWA、ISO 17020/17025）及特定采购部门专有词汇（如科威特水电及可再生能源部 MEWRE、球墨铸铁管、管件、自锚止推接口、双倍厚度水泥砂浆内衬等）；
  - 数字与单位 100% 核实（如 200.00 ppm, 4°C, 150 微米, 2200 kg/cm²）。

### 第三步：高保真矢量页面重构与物理限高 (Layout Reconstruction with Height Guard)
利用标准 HTML5 + CSS `@page` 打印样式进行 1:1 页面映射重构：
- **物理限高与防溢出**：
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
    overflow: hidden; /* 严禁内部元素撑爆高度触发打印机额外分页 */
  }
  .content-area {
    flex: 1;
    overflow: hidden;
  }
  ```
- **公文表头规范**：重构官方中英双语双栏表格框，左侧英文、右侧规范中文，保持 `MEWRE/W.P.S.2026` 等公文编号与签章区；
- **目录点线对齐**：使用 flex 布局与 `border-bottom: 1.2px dotted #555` 实现目录标题与页码的精准对齐；
- **表格与签章区**：保留所有表格网格线、多行合并、签名盖章栏及承诺函框；
- **字体标准**：默认使用标准宋体/黑体矢量字体（`font-family: "SimSun", "Songti SC", "Microsoft YaHei", serif;`），确保公文严肃性与无乱码渲染。

### 第四步：内置引擎渲染与 JS 溢出探针 (Vector Rendering with Overflow Probe)
调用技能内置渲染脚本直接生成纯矢量 PDF，内置 JavaScript 探针会自动检测是否有任何页面产生高度溢出：
```powershell
python "e:\antigravity_workspace\univ\.agent\skills\pdf-translate\scripts\render_pdf.py" "path/to/full_doc.html" "path/to/output_full.pdf"
```

### 第五步：一键自动化对比审计与自愈闭环 (Automated Audit & Self-Repair)
生成 PDF 后，**必须运行技能内置的 `audit_pdf.py` 自动化对比工具**：
```powershell
python "e:\antigravity_workspace\univ\.agent\skills\pdf-translate\scripts\audit_pdf.py" --src "path/to/source.pdf" --tgt "path/to/output_full.pdf"
```

该工具全自动执行 4 大流水线：
1. **页码 1:1 校验**：源文件与目标文件总页数必须完全一致；
2. **纯矢量文字层检验**：位图图片数量必须为 0；
3. **条款编号逐页双向 Diff**：自动扫描每一页的条款编号（如 1.1~1.4, 2.1.1~2.1.8 等），捕获漏项与额外多出项；
4. **AI 幻觉与敷衍词雷达**：自动拦截“技术规范编制综述”、“核对清单”、“暂缺”、“待补充”、“此处略”等常见大模型逃避或捏造词汇。

**自动修复循环**：若 `audit_pdf.py` 报告任何 Critical Error，立即修改对应分块模块的 HTML，重新渲染并二次比对，直到全项 PASS 方可向用户最终交付！

---

## 核心脚本工具箱 (Built-in Scripts)

- **PDF 渲染引擎（含 JS 页面溢出自检）**：
  [`.agent/skills/pdf-translate/scripts/render_pdf.py`](file:///e:/antigravity_workspace/univ/.agent/skills/pdf-translate/scripts/render_pdf.py)
  - 底层基于 Microsoft Edge / Chromium 矢量打印，毫秒级检测 `.page` 物理高度，避免跨页溢出。
- **PDF 1:1 自动化对比审计引擎**：
  [`.agent/skills/pdf-translate/scripts/audit_pdf.py`](file:///e:/antigravity_workspace/univ/.agent/skills/pdf-translate/scripts/audit_pdf.py)
  - 逐页 1:1 扫描源文件与目标文件，深度校验页码对齐、纯矢量层、条款 Diff、数值一致性与反脑补关键字拦截。
