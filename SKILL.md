---
name: pdf-translate
description: "Use when translating PDF documents between languages while strictly preserving original layout, formatting, typography, tables, and signatures. Powered by LLM direct comprehension, two-stage data-contract translation, chunked modular generation, in-browser JS overflow detection, and high-fidelity vector PDF reconstruction. Features zero-hallucination guardrails and automated 1:1 page-by-page audit script (audit_pdf.py)."
version: 2.3.0
author: Antigravity
---

# PDF 保持原排版翻译 Skill (大模型直译 + 几何探针测量 + 矢量排版重构 + 生成后对比自愈)

当用户需要**翻译 PDF 文档**，且要求**必须完整保留原始版面格式、公文表头、目录、双语表格、签章栏、插图物理尺寸**并最终**输出为高保真矢量 PDF 文件**时，使用此 Skill。

> [!IMPORTANT]
> **四大核心铁律（杜绝机翻乱码、长文档幻觉、跨页溢出与图片排版变形）**：
> 1. **严禁脑补，严格忠实直译 (Strict Faithful Translation & Zero Hallucination)**：
>    - **不得压缩或遗漏条款**：逐条忠实翻译每一个一级、二级、三级子条款（如法定资质证照清单 2.1.1~2.1.8、年限指标、年产能门槛 150,000 吨、分卷装订规则 Volume 2A/2B 等），坚决禁止主观总结或合并条款；
>    - **坚决禁止虚构常识**：严禁凭常识脑补原文不存在的交付程序、装订份数、银行授信金额或办事流程（例如原文未写具体金额则绝对禁止编造 1,000,000 KWD，无 5.3 节则绝对不可添加 5.3 节）；
>    - **表格格式 1:1 忠实还原**：官方附表（如 Appendix-1 至 Appendix-6）的列名、行高、选项框、备注及签字盖章区必须严格对齐原件，严禁用自创的“申报核对清单 (Checklist)”或通用表格粗糙代替。
> 2. **几何探针与视觉锚点测量铁律 (Geometry Probe & Visual Anchor Measurement)**：
>    - **绝对禁止经验主义猜度尺寸**：严禁在未测量原件几何信息的情况下，随意给插图或表格加上 `max-height: 220px` 等主观限制，导致原图严重缩水变形或比例失调；
>    - **原图物理坐标与尺寸 1:1 提取**：提取图片时必须调用 `page.get_image_rects(xref)` 获取原图在页面上的实际 `width`、`height` 以及 `x0, y0`，并在 HTML 中严格以真实物理尺寸呈现（如原件宽 218.9pt、高 322.4pt，HTML 中必须按照该物理尺寸渲染）；
>    - **几何线条与装饰框高保真复刻**：通过 `page.get_drawings()` 提取所有几何元素（如顶会论文标题框的 4pt 粗黑顶线与 1pt 细底线、长度 143.5pt 的左对齐短横脚注线），严禁用通用单薄的 100% 宽度边框粗暴替代；
>    - **中文信息密度补偿与垂直基线对齐**：中文字符信息密度通常比西文高 20%~35%，必须记录关键文字块的垂直基准起点 `y0`（如摘要标题、正文、章节起始与脚注线位置），通过微调行高（`line-height: 1.35~1.45`）、段落间距（`margin`）以及灵活运用网格与绝对定位，确保中文版面的视觉重心与垂直基线与原件严密锚定，杜绝页面下半部分突兀大面积留白；
>    - **首页页眉页脚特殊规则**：大部分顶会论文（NIPS/ICML/CVPR 等）或官方公文首页（Page 1）不编排页码，底部通常为会议发表信息或官方备案行，严禁在第一页机械添加页码。
> 3. **两阶段解耦与分块生成 (Schema-First & Chunked Pipeline)**：
>    - **数据与排版分离**：长文档翻译时，优先提取页面结构化数据（条款清单、参数字典、表格行列），再灌入标准化 HTML 模板，严禁一边长篇自由发挥一边写标签；
>    - **单批次生成严禁超过 10 页**：超过 10 页的文档强制按 10 页为单位拆分为独立模块（如 `part1_pages.py`, `part2_pages.py`），避免模型在中后段注意力衰减导致失控。
> 4. **生成后对比质检与用户确认关卡 (Mandatory Audit & User Preview Before Commit)**：
>    - PDF 渲染生成后，**绝不允许直接交付给用户**，必须运行技能内置的 `scripts/audit_pdf.py` 执行页码、矢量层、条款差集与敏感词全面扫描；
>    - 渲染生成 1:1 并排对比图（PNG），**必须在对话中直接展示关键页面对比效果供用户审阅确认**，在获得用户明确许可前严禁擅自 Git Commit 或推送！

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

### 第一步：文档几何探测与结构分块 (Inspection & Geometry Probing)
使用 Python (`fitz` / PyMuPDF) 全面探测文档物理尺寸、插图尺寸、装饰线与关键文本块基线坐标：
```python
import fitz
doc = fitz.open("path/to/document.pdf")
print("Total pages:", len(doc))

for i, page in enumerate(doc):
    print(f"\n=== PAGE {i+1} rect: {page.rect} ===")
    # 1. 探测图片物理尺寸与位置
    for img in page.get_images():
        for r in page.get_image_rects(img[0]):
            print(f"  Image xref {img[0]}: w={r.width:.1f}, h={r.height:.1f}, (x0={r.x0:.1f}, y0={r.y0:.1f})")
    # 2. 探测几何线条与装饰边框
    for d in page.get_drawings():
        r = d['rect']
        if r.width > 30:
            print(f"  Line: w={r.width:.1f}, h={r.height:.1f}, (x0={r.x0:.1f}, y0={r.y0:.1f})")
    # 3. 探测核心文本块垂直基准起点 y0
    for b in page.get_text("blocks"):
        if b[4].strip():
            print(f"  Block ({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}): {b[4].strip()[:40]}")
# 若总页数 > 10 页，强制制定分块规划（如 Part 1: P1~10, Part 2: P11~20 ...）
```

### 第二步：两阶段专业直译（严格无脑补）(Two-Stage Strict Translation)
- **阶段 1（提取与核定）**：先按页提取条款编号、所有数值区间与表格字段，建立精确的翻译数据契约；
- **阶段 2（模板化填装）**：
  - 准确翻译专业术语与国际标准（如 Transformer 自注意力、编码器-解码器架构、BLEU 得分、残差连接；或标书中的 ISO 2531、BS EN 545、AWWA、科威特水电部 MEWRE 等）；
  - 数字、单位与公式 100% 核实（如 200.00 ppm, 4°C, 150 微米, 2200 kg/cm², $d_{\text{model}} = 512$ 等）。

### 第三步：高保真矢量页面重构与物理限高 (Layout Reconstruction with Physical Anchors)
利用标准 HTML5 + CSS `@page` 打印样式进行 1:1 页面映射重构：
- **物理尺寸动态适配与防溢出**：
  根据第一步探测得到的真实页面尺寸定义 `@page`（如 US Letter `size: 8.5in 11in;` 或 A4 `size: 210mm 297mm;`）：
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
    overflow: hidden; /* 严禁内部元素撑爆高度触发打印机额外分页 */
  }
  .content-area {
    flex: 1;
    overflow: hidden;
  }
  ```
- **插图 1:1 物理尺寸渲染**：严格按照第一步测量的 `w` 和 `h` 设定图片的 `width` 与 `height`（如 `width: 218.9pt; height: 322.4pt;`），绝对禁止用经验值限制！
- **几何线条还原**：依据探测出的线条坐标绘制精确线宽与长度（如标题框 4pt 顶线 + 1pt 底线、143.5pt 短横脚注线）；
- **中文垂直基线对齐**：通过段落间距和舒适行高（1.35~1.45）合理分布垂直空间，使各区块垂直起点与原件基线严格对齐；
- **字体标准**：默认使用标准专业矢量字体（英文 Times New Roman，中文 SimSun / Songti SC），确保学术严肃性与无乱码渲染。

### 第四步：内置引擎渲染与 JS 溢出探针 (Vector Rendering with Overflow Probe)
调用技能内置渲染脚本直接生成纯矢量 PDF，内置 JavaScript 探针会自动检测是否有任何页面产生高度溢出：
```powershell
python "e:\antigravity_workspace\univ\.agent\skills\pdf-translate\scripts\render_pdf.py" "path/to/full_doc.html" "path/to/output_full.pdf"
```

### 第五步：自动化对比审计与视觉并排质检 (Automated Audit & Visual Review)
生成 PDF 后，**必须运行技能内置的 `audit_pdf.py` 自动化对比工具并生成对比图**：
```powershell
python "e:\antigravity_workspace\univ\.agent\skills\pdf-translate\scripts\audit_pdf.py" --src "path/to/source.pdf" --tgt "path/to/output_full.pdf"
```

该工具全自动执行 4 大流水线：
1. **页码 1:1 校验**：源文件与目标文件总页数必须完全一致；
2. **纯矢量文字层与关键图片检验**：保留的矢量图片数量完全对应；
3. **条款与关键实体逐页双向 Diff**：自动扫描每一页的条款编号、表名图名，捕获漏项；
4. **AI 幻觉与敷衍词雷达**：自动拦截“技术规范编制综述”、“核对清单”、“暂缺”、“此处略”等常见大模型逃避或捏造词汇。

**用户视觉确认门禁 (User Confirmation Gate)**：
- 渲染原件与译件 1:1 并排对比图（PNG），在会话中直接展示重点页面（如封面、架构图页、复杂表格页）；
- 向用户汇报质检结果与对齐细节，**必须等待用户明确确认满意后，方可执行 Git 提交或任务交付**！

---

## 核心脚本工具箱 (Built-in Scripts)

- **PDF 渲染引擎（含 JS 页面溢出自检）**：
  [`.agent/skills/pdf-translate/scripts/render_pdf.py`](file:///e:/antigravity_workspace/univ/.agent/skills/pdf-translate/scripts/render_pdf.py)
  - 底层基于 Microsoft Edge / Chromium 矢量打印，毫秒级检测 `.page` 物理高度，避免跨页溢出。
- **PDF 1:1 自动化对比审计引擎**：
  [`.agent/skills/pdf-translate/scripts/audit_pdf.py`](file:///e:/antigravity_workspace/univ/.agent/skills/pdf-translate/scripts/audit_pdf.py)
  - 逐页 1:1 扫描源文件与目标文件，深度校验页码对齐、纯矢量层、条款 Diff、数值一致性与反脑补关键字拦截。
